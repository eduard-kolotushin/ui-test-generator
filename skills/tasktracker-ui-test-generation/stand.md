# Стенд для установки Grafana

1) Ссылка на UI: https://st-view-mock-01.opsmon.sbt

2) Адрес сервера, на котором развернута Grafana, и базовый URL API: https://st-view-grafana-01.opsmon.sbt:3000

3) Путь до файла конфигурации: /opt/grafana/conf/gse-plugin.ini

4) Команда запуска службы: `sudo systemctl start/restart grafana-server`

5) Команда подключения к потоку логов: `sudo journalctl -u grafana-server -f`