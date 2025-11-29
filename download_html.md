# download_html.py 使い方

簡単なHTMLダウンロード用スクリプトです。`requests` が利用可能なら `requests` を使い、なければ `urllib` にフォールバックします。

インストール:

```bash
python -m pip install -r requirements.txt
```

使い方:

```bash
# NHK番組IDだけ渡す例（BR8Z3NX7XM -> p=BR8Z3NX7XM_01 を組み立てる）
python download_html.py BR8Z3NX7XM

# ファイルへ保存
python download_html.py BR8Z3NX7XM -o page.html

# タイムアウトを指定（秒）
python download_html.py BR8Z3NX7XM --timeout 10 -o page.html
```

エラー時は標準エラーにメッセージを出して非ゼロで終了します。
