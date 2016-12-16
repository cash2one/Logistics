### 注意

#### 对于客户端和前端:
以后只用关心 `http://10.0.0.199/apidoc/` 这个下面的文档就行了, 是按照需求方来分的目录

#### 对于后端服务器的同学来说:
关心`http://10.0.0.199/doc/` 下面的文档, 这个下面是按照后端层级以及模块来区分的

#### 对于提供文档的同学来说:
只用维护一份文档, 只用使用apidoc生成一次文档, 放在规定的位置, 别的就不用管啦, 系统自动对文档进行归档

---

### 使用流程和场景

小明开发了一个新的模块A, 涉及到api网关层的模块A, 和逻辑层的模块A

他将两个模块分别生成在下面的目录, 文档代码跟随业务代码

```
MrWind-Dispatcher/api_gateway/modelA
MrWind-Dispatcher/business_logic_api/modelA
```

则他需要使用apidoc工具来生成两份文档分别存放在

```
cd MrWind-Dispatcher
apidoc -i ./api_gateway/modelA -o ./doc/api_gateway/modelA
apidoc -i ./business_logic_api/modelA -o ./doc/business_logic_api/modelA
```

然后进行`git add -> git commit -> git push`

完成

### 后台运行说明

系统后台对`git push`进行了一个hook, 大致流程是自动运行下面的命令

```
cd MrWind-Dispatcher
python ./scripts/doc_archive/doc_archive.py -o ./apidoc -- ./doc/api_gateway/*

scp -r ./doc root@10.0.0.199:/var/www/html/
scp -r ./apidoc root@10.0.0.199:/var/www/html/
```

可以发现只有在MrWind-Dispatcher/doc/api_gateway文件夹下面的文档才会被归档, 因为只有这一层的文档才是给前端和客户端同学看的

---

### doc_archive.py使用说明

```
#Archive Apidoc
Usage:
doc_archive.py [-o=<dir>] [--] <docdir>...
doc_archive.py <docdir>... [-o=<dir>]
doc_archive.py -h | --help

Arguments:
    <docdir> 一个或多个有效的apidoc文档目录

Options:
  -h --help     Show this screen.
  --version     Show version.
  -o <dir>      output dir [default: ./apidoc]
```

