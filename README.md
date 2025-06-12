# Dockerized ToDo App (Flask, PostgreSQL, Docker-Compose)

FlaskとPostgreSQLで作成したWeb ToDoアプリを、Docker Composeで完全にコンテナ化したプロジェクトです。

## 特徴
- `docker compose up`コマンド一発で、アプリケーションとデータベースが起動します。
- 開発環境のセットアップが非常に簡単で、誰でも同じ環境を再現できます。

## 動作環境
- Docker
- Docker Compose (Docker Engineのプラグインとして)

## セットアップ & 実行手順

1. **リポジトリをクローン:**
   ```bash
   git clone git@github.com:あなたのユーザー名/docker-todo-app.git
   cd docker-todo-app