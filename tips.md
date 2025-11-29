リモートブランチの状態を確認するためのコマンド
```bash
git fetch --prune
```

すでに削除されたリモートブランチに基づいてローカルブランチを削除する
```bash
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs -r git branch -d
```


プルリクエストを作成
```
#69のプルリクエストを作成
```

```bash
gh pr create --base main --title "feat: convert_racer.py の機能改善と仕様書の更新" --body "convert_racer.py の以下の点を修正しました。

- 生年月日を和暦から西暦に変換する処理を修正
- 年と期の列をCSVの先頭に正しく移動するように修正

また、上記の変更に合わせて、仕様書(convert_racer.md)を更新しました。
- 生年月日のフォーマットを西暦に変更
- 詳細成績データの項目をすべて記載
- データ整形のルールを詳細化"  
```
