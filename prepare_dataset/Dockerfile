# Используем официальный образ MFA как базовый
FROM mmcauliffe/montreal-forced-aligner:latest

# Скачиваем акустическую модель английского языка
RUN mfa model download acoustic english_mfa

# Скачиваем словарь английского языка
RUN mfa model download dictionary english_us_arpa

RUN mfa models download g2p english_us_mfa

# Рабочая директория внутри контейнера
WORKDIR /data

# По умолчанию запускаем интерактивный терминал
CMD ["/bin/bash"]
