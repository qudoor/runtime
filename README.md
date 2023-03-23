# QuPot

## 初始化配置
```shell
# output
python manage.py dumpdata runtime.runtimeappmodel   --output=fixtures/initial_data.json

# input
python manage.py loaddata fixtures/initial_data.json
```