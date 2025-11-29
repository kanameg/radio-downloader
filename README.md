# NHKラジオダウンロードプログラム
## 概要
NHKラジオの番組をダウンロードするためのPythonコードです。番組の取得、保存、管理を行います。


## Playwright のインストール（ワンライナー）

Playwright を使ってページを正しく取得する場合、実行する Python 環境に Playwright 本体とブラウザをインストールする必要があります。簡単なワンライナー例:

```bash
# 仮想環境を有効にした後、または使用する Python で実行
pip install --upgrade pip setuptools wheel && pip install playwright && python -m playwright install chromium
```

補足:
- Debian/Ubuntu 系ではネイティブ依存が必要な場合があります。その場合は以下を実行してください（sudo が必要です）:

```bash
sudo apt-get update && sudo apt-get install -y libasound2 libgbm1 libgtk-3-0 libxss1 libnss3 libx11-xcb1 libxtst6 libx11-6 ca-certificates fonts-liberation
# その後、ブラウザ依存をインストール
python -m playwright install-deps
```

問題が発生した場合は、使用している Python 実行ファイルが想定通りか（`which python` や `which python3`）、そして `pip list` に `playwright` が含まれているかを確認してください。

