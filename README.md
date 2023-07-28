# リポジトリの説明

## 初期設定
```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pipenv
pipenv sync --dev
cdk ls
```

## デプロイ手順
### Route53でドメインを取得する
マネジメントコンソールからRoute53でドメインを取得する
(ドメインを新規取得していない場合は、ホストゾーンが作成されているかを確認する)

### pipelineにてGithubリポジトリとの接続を作成する
マネジメントコンソールからpipelineにてGithubリポジトリとの接続を作成する

### コンフィグファイル記載
configs/config.yamlに必要情報を記載する

### ネットワークスタックデプロイ
```
cdk synth PipelineStack/ApplicationStage/NetworkStack  #デプロイ前のvalidationコマンド
cdk deploy PipelineStack/ApplicationStage/NetworkStack  #リソースがデプロイされるため注意
```

### データベーススタックデプロイ
```
cdk synth PipelineStack/ApplicationStage/DatabaseStack  #デプロイ前のvalidationコマンド
cdk deploy PipelineStack/ApplicationStage/DatabaseStack  #リソースがデプロイされるため注意
```

### データベースのテーブル・ユーザ作成
①ネットワークスタックで作成したVPC内にCloud9環境を作成する
②Cloud9環境で以下のコマンドを実行する。
```
# RDSエンドポイントとRDSのルートパスワードはSecretsManagerから参照すること
$ mysql -h RDSエンドポイント -u rdsmaster -p
password: RDSのルートパスワード

SQL> create database wordpress;
SQL> grant all privileges on wordpress.* to wordpress@'%' identified by 'wordpress';
SQL> quit
```
③SecretsManagerのDBAccessに設定したデータベース名、ユーザ名、パスワードを設定する

### サービススタックデプロイ
```
cdk synth PipelineStack/ApplicationStage/ServiceStack  #デプロイ前のvalidationコマンド
cdk deploy PipelineStack/ApplicationStage/ServiceStack  #リソースがデプロイされるため注意
```

###AWS Certificate Managerの証明書のレコードを作成
Certificate Managerの証明書のレコードを作成を作成しないとデプロイが進めないので、
以下の手順でレコードを追加する。
証明書を選択 > Route53 でレコードを作成 > レコードを作成

### ワードプレスインストール
ワードプレスのインストールがされていないと、
サービススタックデプロイ中にロードバランサーのヘルスチェックでエラーとなるので、
コンテナが起動している間にロードバランサーのエンドポイントからアクセスし、
ワードプレスのインストールを実施する。

### パイプラインスタックデプロイ
Gitリポジトリのconfigで指定したブランチにプッシュする
```
cdk synth #デプロイ前のvalidationコマンド
cdk deploy #リソースがデプロイされるため注意
```
