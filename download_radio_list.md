```markdown
# download_radio_list.py 使い方

番組一覧を JSON で出力するスクリプト `download_radio_list.py` の使い方。

インストール:

```bash
python -m pip install -r requirements.txt
```

使い方:

```bash
# NHK番組IDだけ渡す例（BR8Z3NX7XM -> p=BR8Z3NX7XM_01 を組み立てる）
python download_radio_list.py BR8Z3NX7XM

# JSONファイルへ保存
python download_radio_list.py BR8Z3NX7XM -o programs.json

# タイムアウトを指定（秒）
python download_radio_list.py BR8Z3NX7XM --timeout 10 -o programs.json
```

出力は JSON 配列で、各要素は以下のキーを持ちます:

- `title`: 番組名
- `broadcast_date`: 放送日（YYYY-MM-DD）
- `broadcast_start`: 放送開始時刻（ISO 形式）
- `hls_url`: `index.m3u8` のURL

エラー時は標準エラーにメッセージを出して非ゼロで終了します。

```
