# ProxyCollect

## Features

- [x] Crawl
- [x] Valid
  - [x] http
  - [x] https
  - [ ] socks4
  - [ ] socks5
- [x] Command
  - [x] crawl
  - [x] query
  - [x] valid
- [x] DB
  - [x] mysql
  - [ ] redis
- [ ] Web
  - [x] Query
  - [ ] Auth
  - [ ] Control Panel

## Quick Start

### Database

#### Create DB

Import [db.sql](./db.sql) to your database. It will create a schama named `proxy_ip`, you can change this schama name later.

```sql
source db.sql;
```

#### Create DB User

You'd better to create a user which has all CRUD privileges for this database.

**Do not use root user.**

```sql
create user '<username>'@'<host>' identified by '<passWord>';
grant all privileges on proxy_ip.* to '<username>'@'<host>';
```

Host could be `localhost` to deny remote connections. Or `%` to allow all.

Set host to `localhost` is recommend.

### Minimal Config

You can add configuration file `config.json` or through system environments to set configs.

#### Set DB Configs

Suggest using sys env to set security text, such as password.

```sh
export PC_DB_RDB_HOST=<host>
export PC_DB_RDB_USERNAME=<username>
export PC_DB_RDB_PASSWORD=<password>
```

`<host>` is host ip address of your database.

### Crawl

1. Set config

    Crawl's config is required and cann't set through system environment.

    ```json
    {
        "crawl": {
            "crawlers": [
                {
                    "callable": "kuaidaili",
                    "args": [1,5],
                    "kwargs": {
                        "timeout": 5
                    }
                },
                {...}
            ]
        }
    }
    ```

    `callable` is the name of crawler.

    `args` and `kwargs` are this callable's parameters.

2. Run

    ```sh
    python command.py c
    ```

### Valid

```sh
python command.py v
```

## Config

Most of configs can set through system environment, but only support string and numbers, dict and list are not supported.

All sys env must starts with `PC_`.


## Extend

### DB Support

It is designed to support multiple storages, such as mysql, oracle, mongodb, redis and so on.

And [DbUtil](./db/dbutil.py) is the common entry point.

### Crawlers

You can add your own crawlers and config in `crawl.crawlers.callable` with full-qualified function name, such as `crawl.crawler.kuaidaili`.

## Develop

### Prepare

It is developed in vscode with docker desktop.

Select `Remote-Containers: Open folder in container`.

You have to prepare the database. Set system environments in `.env` file as below.

```env
PC_DB_RDB_HOST=<host>
PC_DB_RDB_USERNAME=<username>
PC_DB_RDB_PASSWORD=<password>
PC_DB_RDB_DB=<database name>
```

And a simple config file(`config.json`) to run commands.

```json
{
    "$schema": "./config-schema.json",
    "crawl": {
        "crawlers": [
            {
                "callable": "kuaidaili",
                "args": [
                    1,
                    2
                ]
            }
        ]
    }
}
```

### Coverage

```py
python -m coverage run --omit "**/*/__init__.py","tests/**/*" -m unittest discover ./tests -p *_test.py
python -m coverage report
```
