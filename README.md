# クエ監視カメラ送信側

カメラから取得したデータをDropboxにアップロードする。

# 概要

OpenCVでカメラ画像を取得してDropboxにアップロードする。カメラ画像の取得はセッションという単位で行われ、1回のセッション中で等間隔に複数のカメラ画像が取得される。

# 動かし方

1. Dropboxのアクセストークンを取得する。（参考：https://zerofromlight.com/blogs/detail/121/ ）
2. [main.py](./main.py)があるディレクトリに`cd`する。
3. 「設定の定義」に従って設定を定義する。
4. [main.py](./main.py)を実行する。

# 設定の定義

手順2で移動したカレントディレクトリに「settings.json」というファイルを作り、次のフィールドを定義する。

|                変数名                 |  型  |                    内容                     |          例          |
|:----------------------------------:|:---:|:-----------------------------------------:|:-------------------:|
|       `DROPBOX_ACCESS_TOKEN`       | 文字列 |             Dropboxのアクセストークン              |   （取得したアクセストークン）    |
|     `CAPTURE_TMP_FOLDER_PATH`      | 文字列 |       カメラから取得した画像を一時的に保存するフォルダへのパス        | `"./__capture_tmp"` |
|            `CAMERA_ID`             | 整数  | OpenCV（`cv2.VideoCapture`）がカメラを開くときのカメラ番号 |         `0`         |
| `SESSION_CAPTURE_INTERVAL_SECONDS` | 小数  |         1回のセッション中でカメラ画像を取得する間隔（秒）         |        `0.5`        |
|        `SESSION_N_CAPTURES`        | 整数  |          1回のセッション中でカメラ画像を取得する回数           |        `20`         |
|     `INTERVAL_SESSION_SECONDS`     | 小数  |              セッションを繰り返す間隔（秒）              |        `300`        |
|       `MAX_UPLOAD_SESSIONS`        | 整数  |            アップロードするセッション数の最大値             |       `1024`        |

上記の「例」で示したフィールドを定義した「settings.json」はこんな感じ：

```json
{
  "DROPBOX_ACCESS_TOKEN": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "CAPTURE_TMP_FOLDER_PATH": "./__capture_tmp",
  "CAMERA_ID": 0,
  "SESSION_CAPTURE_INTERVAL_SECONDS": 0.5,
  "SESSION_N_CAPTURES": 20,
  "INTERVAL_SESSION_SECONDS": 300,
  "MAX_UPLOAD_SESSIONS": 1024
}
```

上記の「例」の設定では、各セッションは300秒間隔で実行される。各セッションは0.5秒間隔で20枚のカメラ画像を取得する。各セッションはzipファイルとしてDropboxにアップロードされる。

Dropboxには最新の1024セッションがアップロードされ、アップロードされているセッション数が1024を超えた場合は古いセッションから削除される。

# アップロードされるファイルの概要

- 各セッションはzipファイルでアップロードされる
    - zipファイルのファイル名は「＜タイムスタンプ＞.zip」の形式
    - ＜タイムスタンプ＞はアップロードの時刻（unix時刻）
- 各セッションのzipファイルの中身はカメラ画像とメタデータ
    - カメラ画像：JPEG画像
        - ファイル名は「＜画像番号＞.jpeg」の形式
        - ＜画像番号＞は画像を取得した順に連番で付与される
    - メタデータ：JSON
        - `success`：取得が正常に終了した場合は`true`、異常終了した場合は`false`
        - `reason`：取得が正常に終了した場合は`null`、異常終了した場合は理由を表す文字列
        - `count`：取得したカメラ画像の枚数
        - `timestamps`：各カメラ画像を取得した時刻（ISO形式）のリスト
    