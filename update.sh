#!/bin/bash
# -*- coding: utf-8 -*-

# データを最新にダウンロード・更新するスクリプト
# 使用方法: ./update.sh 2025-07-13
# 指定日からデータの最新日まで番組表を変換し、翌日の番組表を取得します

set -e  # エラーが発生した場合にスクリプトを終了

# 引数チェック
if [ $# -ne 1 ]; then
    echo "使用方法: $0 YYYY-MM-DD"
    echo "例: $0 2025-07-13"
    echo "指定日からデータの最新日まで番組表を変換し、翌日の番組表を取得します"
    exit 1
fi

# convert_programs.shの存在確認
if [ ! -f "./convert_programs.sh" ]; then
    echo "エラー: convert_programs.sh が見つかりません"
    exit 1
fi

# 日付の解析
TARGET_DATE=$1

# 日付形式の検証
if ! [[ "$TARGET_DATE" =~ ^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$ ]]; then
    echo "エラー: 日付はYYYY-MM-DD形式で入力してください: $TARGET_DATE"
    exit 1
fi

# 日付の妥当性チェック
if ! date -d "$TARGET_DATE" > /dev/null 2>&1; then
    echo "エラー: 無効な日付です: $TARGET_DATE"
    exit 1
fi

# データの最新日を取得（番組表ファイルから判断）
LATEST_PROGRAM_FILE=$(ls data/raw/programs/b*.txt 2>/dev/null | sort | tail -1)
if [ -z "$LATEST_PROGRAM_FILE" ]; then
    echo "エラー: 番組表データファイルが見つかりません"
    exit 1
fi

# ファイル名から番組表の最新日を抽出（例：b250723_u8.txt → 2025-07-23）
LATEST_PROGRAM_FILENAME=$(basename "$LATEST_PROGRAM_FILE")
LATEST_PROGRAM_DATE_STR=${LATEST_PROGRAM_FILENAME:1:6}  # b250723_u8.txt から 250723 を抽出
LATEST_PROGRAM_DATE="20${LATEST_PROGRAM_DATE_STR:0:2}-${LATEST_PROGRAM_DATE_STR:2:2}-${LATEST_PROGRAM_DATE_STR:4:2}"

# データの最新日を取得（競走結果ファイルから判断）
LATEST_RESULT_FILE=$(ls data/raw/results/k*.txt 2>/dev/null | sort | tail -1)
if [ -z "$LATEST_RESULT_FILE" ]; then
    echo "警告: 競走結果データファイルが見つかりません（初回実行時は正常）"
    LATEST_RESULT_DATE="$TARGET_DATE"
else
    # ファイル名から競走結果の最新日を抽出
    LATEST_RESULT_FILENAME=$(basename "$LATEST_RESULT_FILE")
    LATEST_RESULT_DATE_STR=${LATEST_RESULT_FILENAME:1:6}  # r250722_u8.txt から 250722 を抽出
    LATEST_RESULT_DATE="20${LATEST_RESULT_DATE_STR:0:2}-${LATEST_RESULT_DATE_STR:2:2}-${LATEST_RESULT_DATE_STR:4:2}"
fi

echo "番組表最新日: $LATEST_PROGRAM_DATE"
echo "競走結果最新日: $LATEST_RESULT_DATE"

# 指定日と番組表最新日の比較
TARGET_EPOCH=$(date -d "$TARGET_DATE" +%s)
LATEST_PROGRAM_EPOCH=$(date -d "$LATEST_PROGRAM_DATE" +%s)

# if [ "$TARGET_EPOCH" -gt "$LATEST_PROGRAM_EPOCH" ]; then
#     echo "エラー: 指定日($TARGET_DATE)が番組表の最新日($LATEST_PROGRAM_DATE)より後です"
#     exit 1
# fi

# 対象日のepoch秒を取得
TARGET_EPOCH=$(date -d "$TARGET_DATE" +%s)

# 翌日のepoch秒を計算（24時間 = 86400秒を足す）
NEXT_EPOCH=$((TARGET_EPOCH + 86400))

# 翌日の日付を取得
NEXT_DATE=$(date -d "@$NEXT_EPOCH" +%Y-%m-%d)

# データ変換処理の開始日を固定
START_DATE="2025-01-01"

echo "========================================="
echo "競艇予測処理開始"
echo "指定日: $TARGET_DATE"
echo "開始日: $START_DATE"
echo "番組表最新日: $LATEST_PROGRAM_DATE"
echo "競走結果最新日: $LATEST_RESULT_DATE"
echo "翌日: $NEXT_DATE"
echo "========================================="

# 1. 本日までの競走結果データを取得
echo ""
echo "----------------------------------------------------"
echo "1. 本日までの競走結果データを取得中..."

# 競走結果最新日の翌日から指定日までをダウンロードする
# LATEST_RESULT_DATE は上で算出済み（競走結果ファイルがなければ TARGET_DATE が設定されている）
START_RESULT_DATE=$(date -d "$LATEST_RESULT_DATE + 1 day" +%Y-%m-%d)

if [ "$(date -d "$START_RESULT_DATE" +%s)" -le "$(date -d "$TARGET_DATE" +%s)" ]; then
    CUR_DATE="$START_RESULT_DATE"
    while [ "$(date -d "$CUR_DATE" +%s)" -le "$(date -d "$TARGET_DATE" +%s)" ]; do
        echo "Downloading race results for $CUR_DATE"
        ./download_race.sh r "$CUR_DATE"
        # 次の日へ
        CUR_DATE=$(date -d "$CUR_DATE + 1 day" +%Y-%m-%d)
    done
else
    echo "競走結果の新規ダウンロードは不要です（開始日: $START_RESULT_DATE, 指定日: $TARGET_DATE）"
fi

# 2. 翌日の番組表データを取得
echo ""
echo "----------------------------------------------------"
echo "2. 番組表データを取得中..."

# 番組表最新日の翌日から指定日の翌日(NEXT_DATE)までをダウンロードする
# LATEST_PROGRAM_DATE は上で算出済み
START_PROGRAM_DATE=$(date -d "$LATEST_PROGRAM_DATE + 1 day" +%Y-%m-%d)

if [ "$(date -d "$START_PROGRAM_DATE" +%s)" -le "$(date -d "$NEXT_DATE" +%s)" ]; then
    CUR_DATE="$START_PROGRAM_DATE"
    while [ "$(date -d "$CUR_DATE" +%s)" -le "$(date -d "$NEXT_DATE" +%s)" ]; do
        echo "Downloading program (番組表) for $CUR_DATE"
        ./download_race.sh p "$CUR_DATE"
        # 次の日へ
        CUR_DATE=$(date -d "$CUR_DATE + 1 day" +%Y-%m-%d)
    done
else
    echo "番組表の新規ダウンロードは不要です（開始日: $START_PROGRAM_DATE, 取得対象終了: $NEXT_DATE）"
fi

## 数秒待ち
sleep 2  # ダウンロード完了を待つためのスリープ

# 3. 指定日から最新日までの番組表データを変換
echo ""
echo "----------------------------------------------------"
echo "3. 番組表データ変換中（$START_DATE 〜 $NEXT_DATE）..."
./convert_programs.sh "$START_DATE" "$NEXT_DATE"

# 4. 競走結果データを変換
echo ""
echo "----------------------------------------------------"
echo "4. 競走結果データ変換中（$START_DATE 〜 $TARGET_DATE）..."
./convert_results.sh "$START_DATE" "$TARGET_DATE"

echo "========================================="
echo "データ更新処理完了"
echo "番組表処理範囲: $START_DATE 〜 $NEXT_DATE"
echo "競走結果処理範囲: $START_DATE 〜 $TARGET_DATE"
echo "番組表: 変換済み"
echo "競走結果: 変換済み"
echo "翌日番組表($NEXT_DATE): 取得済み"
echo "========================================="

# 5. Gitにコミット
echo ""
echo "----------------------------------------------------"
echo "5. Gitへのコミットを確認中..."

# 変更があるか確認
if [ -n "$(git status --porcelain data/raw/programs/ data/raw/results/ data/programs.csv data/results.csv)" ]; then
    echo "データが更新されました。コミットを実行します。"
    
    # 現在のブランチを保存
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # mainブランチに切り替え
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo "現在のブランチは $CURRENT_BRANCH です。"
        echo "mainブランチに切り替えます..."
        git checkout main
    fi
    
    git add data/raw/programs/* data/raw/results/* data/programs.csv data/results.csv
    git commit -m "Update data for $TARGET_DATE"
    
    # 元のブランチに戻す
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo "$CURRENT_BRANCH ブランチに戻ります..."
        git checkout "$CURRENT_BRANCH"
    fi
    
    echo "========================================="
    echo "Gitコミット完了"
    echo "========================================="
else
    echo "データに更新はありませんでした。コミットをスキップします。"
fi
