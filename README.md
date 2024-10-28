# Sobaken-ID
Цель проекта попробовать сделать Computer Vision сервис для поиска пропавших животных на просторах интернета.  

## Проблема
- На простом человеческом: "поиск животных по отличительным особенностям: размер, цвет, паттерн на шерсти, отрезано ухо, сломан хвост, ошейник и так далее. С поправкой на погоду/освещение/состояние животного/грязь на шерсти/лишние объекты на фотке."
- С технической точки зрения, так как это поиск то возможно подойдёт word2vec подход (или точнее img2vec). То есть, например, строим базу векторов доступных животных в БД (id животного -> вектор из последнего слоя модели + доп фичи) и для каждого нового животного генерируем тот же самый вектор от той же модели и ищем по базе.

<details>
  <summary>Особенности</summary>
1. Ложно отрицательные результаты критичны. Плохо если из выборки пропадает целевое животное. С другой стороны если мы выдаём больше ложно положительных то человек может сам доискать животное (в разумных количествах и отсортированных по уменьшению схожести).
2. На первых этапах важнее сфокусироваться на собаках - их намного сложнее пристраивать, лечить, передерживать и так далее.
</details>

# Первые результаты
На скринах в первой колонке фото-запрос, остальные 5 колонок это то что модель подобрала как наиболее подходящее из примерно 500 фоток животных которых **модель не видела на тренировке** (1000 фото - train, 500 - test)  

1.
<img width="1594" alt="Screenshot 2024-10-24 at 11 54 51" src="https://github.com/user-attachments/assets/9b33d7c0-047b-4e57-b3ac-160e4ed9d80c">
2.  
<img width="1674" alt="Screenshot 2024-10-24 at 11 56 07" src="https://github.com/user-attachments/assets/3bc6e2c4-3681-49fd-9fe0-4f12a12ea21d">
3.  
<img width="1715" alt="Screenshot 2024-10-24 at 11 57 32" src="https://github.com/user-attachments/assets/222d39be-dd5c-4e4e-9889-f0f0238a868f">



**И это учитывая экстремально маленький датасет в 1000 фотографий**! Сейчас мы готовим датасет из 60 тысяч фотографий.

### Как это работает
- Как это устроенно внутри - пример карты температур показывает "куда смотрит модель" при генерации векторов схожести:
- <img width="1719" alt="heat" src="https://github.com/user-attachments/assets/33f55772-c99d-4837-9555-d8035cda01e2">


### Как запустить локально
- установить Poetry
- `poetry shell` из рута проекта
- Скачать данные, настроить пути до них в нужном файле, помолиться что сработает и запустить!

# Контакты
Мой Телеграм [@kella18](https://t.me/kella18)
