import configparser
from typing import Optional

import consul
from dataclasses import dataclass

c = consul.Consul()


@dataclass
class RedisConfig:
    host: str
    password: str
    username: Optional[str]
    port: int


@dataclass
class PostgresConfig:
    database: str
    host: str
    port: int
    username: str
    password: str


@dataclass
class DbConfig:
    postgresql: PostgresConfig
    redis: Optional[RedisConfig]


@dataclass
class Contact:
    name: str
    url: str
    email: str


@dataclass
class Email:
    isTLS: bool
    isSSL: bool
    host: str
    password: str
    user: str
    port: int


@dataclass
class JWT:
    JWT_ACCESS_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str


@dataclass
class Base:
    name: str
    description: str
    vers: str
    jwt: JWT
    contact: Contact


@dataclass
class Config:
    debug: bool
    base: Base
    email: Email
    db: DbConfig


class KVManager:

    def __init__(self, kv):
        self.config = kv
        self.path_list = ["milk-back"]

    def __getitem__(self, node: str):
        self.path_list.append(node)
        return self

    def value(self):
        path = "/".join(self.path_list)
        return self.config.get(path)[1]["Value"].decode('utf-8')


def load_config() -> Config:
    config = consul.Consul().kv
    return Config(
        debug=bool(int(KVManager(config)["milk-back"]["debug"].value())),
        base=Base(
            name=KVManager(config)["milk-back"]["base"]["name"].value(),
            description=KVManager(config)["milk-back"]["base"]["description"].value(),
            vers=KVManager(config)["milk-back"]["base"]["vers"].value(),
            contact=Contact(
                name=KVManager(config)["milk-back"]["base"]["contact"]["name"].value(),
                url=KVManager(config)["milk-back"]["base"]["contact"]["url"].value(),
                email=KVManager(config)["milk-back"]["base"]["contact"]["email"].value()
            ),
            jwt=JWT(
                JWT_ACCESS_SECRET_KEY=KVManager(config)["milk-back"]["base"]["jwt"]["JWT_ACCESS_SECRET_KEY"].value(),
                JWT_REFRESH_SECRET_KEY=KVManager(config)["milk-back"]["base"]["jwt"]["JWT_REFRESH_SECRET_KEY"].value()
            )
        ),
        db=DbConfig(
            postgresql=PostgresConfig(
                host=KVManager(config)["milk-back"]["database"]["postgresql"]["host"].value(),
                port=int(KVManager(config)["milk-back"]["database"]["postgresql"]["port"].value()),
                username=KVManager(config)["milk-back"]["database"]["postgresql"]["username"].value(),
                password=KVManager(config)["milk-back"]["database"]["postgresql"]["password"].value(),
                database=KVManager(config)["milk-back"]["database"]["postgresql"]["name"].value()
            ),
            redis=RedisConfig(
                host=KVManager(config)["milk-back"]["database"]["redis"]["host"].value(),
                username=None,
                password=KVManager(config)["milk-back"]["database"]["redis"]["password"].value(),
                port=int(KVManager(config)["milk-back"]["database"]["redis"]["port"].value())
            )
        ),
        email=Email(
            isTLS=bool(int(KVManager(config)["milk-back"]["email"]["isTLS"].value())),
            isSSL=bool(int(KVManager(config)["milk-back"]["email"]["isSSL"].value())),
            host=KVManager(config)["milk-back"]["email"]["host"].value(),
            port=int(KVManager(config)["milk-back"]["email"]["port"].value()),
            user=KVManager(config)["milk-back"]["email"]["user"].value(),
            password=KVManager(config)["milk-back"]["email"]["password"].value()
        )
    )


def load_docs(filename: str) -> 'configparser.ConfigParser':
    """
    Загружает документацию из docs файла

    :param filename: *.ini
    :return:
    """
    docs = configparser.ConfigParser()
    docs.read(filenames=f"./docs/{filename}", encoding="utf-8")
    return docs
