# Sobaken-ID
Цель проекта попробовать сделать Computer Vision сервис для поиска пропавших животных на просторах интернета.  

## Проблема
- На простом человеческом: "поиск животных по отличительным особенностям: размер, цвет, паттерн на шерсти, отрезано ухо, сломан хвост, ошейник и так далее. С поправкой на погоду/освещение/состояние животного/грязь на шерсти/лишние объекты на фотке."
- С технической точки зрения, так как это поиск то возможно подойдёт word2vec подход (или точнее img2vec). То есть, например, строим базу векторов доступных животных в БД (id животного -> вектор из последнего слоя модели + доп фичи) и для каждого нового животного генерируем тот же самый вектор от той же модели и ищем по базе.

- Аналог в США https://petcolove.org/lost, что-то в этом же духе в Китае https://www.thetimes.com/world/article/chinese-dogs-take-id-cards-on-the-nose-2zh3r0b75

### Особенности:
1. Ложно отрицательные результаты критичны. Плохо если из выборки пропадает целевое животное. С другой стороны если мы выдаём больше ложно положительных то человек может сам доискать животное (в разумных количествах и отсортированных по уменьшению схожести).
2. На первых этапах важнее сфокусироваться на собаках - их намного сложнее пристраивать, лечить, передерживать и так далее.

## Задачи
https://github.com/users/kell18/projects/1/views/1

## Данные
### Сырые данные собранные из VK
- [vk.com/dom_lapkin](https://disk.yandex.ru/d/wFBXsKolqyFRSg), каждый архив содержит индексный файл со всей необходимой информацией, [пример](https://github.com/kell18/sobaken-id/blob/master/scraping/resources/example-index.json)

### Размеченные датасеты что я нашёл в открытом доступе:
- https://www.robots.ox.ac.uk/~vgg/data/pets/
- https://cg.cs.tsinghua.edu.cn/ThuDogs/
- Доп инфу собрал [тут](more-on-data.md)

### Неразмеченные данные - максимально приближенные к реальности
- Любые паблики с потеряшками в ВК, например [vk.com/agatalifenews](https://vk.com/agatalifenews) - могу спарсить сырых данных, скажите если нужно
- Спец сайты для поиска животных вроде [pet911.ru](https://pet911.ru/) (кстати они готовы внедрить такую модель)

**Я помогу разметить данные вручную как станет понятно что и как именно размечать.**


# Дальнейшая интеграция
- У меня есть контакт с [pet911.ru](https://pet911.ru) - они готовы внедрить
- Так же есть идея сделать интеграцию для поиска через приложения ВК для тех же [пабликов потеряшек](https://vk.com/agatalifenews)
- Пытаюсь достучаться до https://teddyfood.com/ чтобы так же интегрироваться с ними

# Контакты
Мой Телеграм @kella18
