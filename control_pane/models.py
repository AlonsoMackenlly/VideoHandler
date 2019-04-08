from django.db import models


class DronePlane(models.Model):
    name_verbose = "Название"
    name = models.CharField(max_length=200, verbose_name=name_verbose)
    camera = models.CharField(max_length=200, verbose_name="Камера")
    state = models.CharField(max_length=200, verbose_name="Состояние")
    state_doors = models.CharField(max_length=200, verbose_name="Состояние дверей")
    state_guides = models.CharField(max_length=200, verbose_name="Состояние направляющих")
    state_lift = models.CharField(max_length=200, verbose_name="Состояние платформы")
    state_luk = models.CharField(max_length=200, verbose_name="Состояние люка")
    coordinates_lat = models.CharField(max_length=200, verbose_name="Координаты (широта)", default="53.474011")
    coordinates_lon = models.CharField(max_length=200, verbose_name="Координаты (долгота)", default="49.203084")
    command = models.CharField(max_length=200, verbose_name="Команда")
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)

    def __str__(self):
        return "База: " + self.name

    class Meta:
        verbose_name = "База"
        verbose_name_plural = "Базы"


class Stream(models.Model):
    id = models.AutoField(primary_key=True)

    # Обязательные поля для заполнения
    title = models.CharField('Название', max_length=100)
    stream_in = models.CharField('Ссылка на поток', default="http://www.example.com", max_length=200)
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)

    #   Перекодирование в ЭТОТ протокол
    protocol = models.CharField('Протокол передачи', default="mjpeg", max_length=200)

    # Автозаполняющиеся
    record_path = models.CharField('Путь сохранения видео',
                                   default="root/drone/{{title}}/record/", max_length=200)
    tmp_image_path = models.CharField('Путь сохранения картинки', default="root/drone/{{title}}/last_image",
                                      max_length=200)
    status = models.BooleanField('Статус', default=False, max_length=2)
    nn_required = models.BooleanField('Слой нейросети', default=False)
    telemetry_required = models.BooleanField('Слой телеметрии', default=False)
    width = models.IntegerField('Ширина', default=0)
    height = models.IntegerField('Высота', default=0)
    fps = models.IntegerField('Кадров в секунду', default=0)

    @classmethod
    def create(cls, title, stream_input, nn_required, width=0, height=0, fps=0):
        new_stream = cls(title=title, stream_input=stream_input, nn_required=nn_required, width=width, height=height,
                         fps=fps)
        return new_stream

    @classmethod
    def create_json(cls, json_parsed):
        return cls(title=json_parsed['title'],
                   stream_in=json_parsed['stream_in'],
                   uid=json_parsed['uid'])

    def init(self):
        self.record_path = "root/drone/%s/record/" % self.title
        self.tmp_image_path = "root/drone/%s/last_image" % self.title

    def to_str(self):
        return "title - %s," \
               " stream_in - %s," \
               " uid - %s," \
               " record_path - %s," \
               " tmp_image_path - %s," \
               " status - %s ," \
               " nn_required - %s," \
               " telemetry_required - %s," \
               " width - %s ," \
               " height - %s ," \
               " fps - %s" % (
                   self.title,
                   self.stream_in,
                   self.uid,
                   self.record_path,
                   self.tmp_image_path,
                   self.status,
                   self.nn_required,
                   self.telemetry_required,
                   self.width,
                   self.height,
                   self.fps
               )

    def __str__(self):
        return "%d. %s" % (self.id, self.title)


# class Camera(models.Model):
#     name = models.CharField(max_length=200)
#     connection_string = models.CharField(max_length=200, default="/")
#     status = models.BooleanField("Статус", default=False) #
#     telemetry_layer = models.BooleanField("Слой телеметрии", default=False) # Слой телеметрии
#     nn_layer = models.BooleanField("Слой нейросети", default=False) # Обработка нейросетями
#     output_name = models.CharField(max_length=200) # MJPEG
#     record_path = models.CharField(max_length=200) # Путь сохранения
#     tmp_image_path = models.CharField(max_length=200) # Путь сохранения последней картинки
#     uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)

class Drone(models.Model):
    name_verbose = "Дрон"
    # name_verbose_plural = "Дроны"
    name = models.CharField(max_length=200, verbose_name=name_verbose)
    connection_ip = models.CharField(max_length=200)
    camera_color_verbose = "Цветная камера"
    camera_color = models.ForeignKey(Stream, on_delete=models.CASCADE, blank=True, null=True, related_name='camera_color')
    camera_thermal_verbose = "Термальная камера"
    camera_thermal = models.ForeignKey(Stream, on_delete=models.CASCADE, blank=True, null=True, related_name='camera_thermal')
    outer_id = models.CharField('Удаленный ID', max_length=200, blank=True, null=True)
    drone_plane = models.ForeignKey(DronePlane, on_delete=models.CASCADE, default=1)
    work_air_speed = models.FloatField("Air speed", default=2)
    work_ground_speed = models.FloatField("Ground speed", default=5)
    work_altitude = models.FloatField("Work altitude", default=30)
    rtl = models.CharField("Домашняя точка", max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Дрон"
        verbose_name_plural = "Дроны"


class Route(models.Model):
    commands = models.TextField(
        verbose_name="Координаты точек")  # TODO: не корректно! изменить на commands ! #coordinates
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, verbose_name="Коптер", blank=True, null=True)
    is_done = models.BooleanField("Выполнено", default=False)
    status = models.CharField('Статус', max_length=200, default="0")
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)
    is_sync = models.BooleanField("Синхронизировано", default=False)

    # type_choices = ('waypoints', 'do_set_')
    # type = models.CharField("Type", default="waypoints")
    def __str__(self):
        return "Маршрут: " + str(self.id)

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"


class DroneCommand(models.Model):
    type = models.CharField('Тип команды', max_length=200, blank=True, null=True)
    point = models.CharField('Координаты', max_length=200, blank=True, null=True)
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, verbose_name="Коптер", blank=True, null=True)
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)
    status = models.CharField("Статус", max_length=200,
                              default="0")  # 0 - новая, 1 - маршрут запущен, 2 - команда выполняется в текущий момент, 3 - завершена, 4 - отменена
    is_sync = models.BooleanField("Синхронизировано", default=False)
    is_async = models.BooleanField("Асинхронность", default=False)
    route_uid = models.CharField('Уникальный идентификатор маршрута', max_length=200, blank=True, null=True)
    outer_id = models.CharField('Внешний ID', max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField('Сортировка', default=1)

    def __str__(self):
        return "Команда: " + str(self.id)

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"


class ExchangeObject(models.Model):
    type = models.CharField(
        "Тип объекта",
        max_length=200,
        blank=True,
        null=True
    )
    uid = models.CharField(
        "УИД",
        max_length=200,
        blank=True,
        null=True
    )

    def __str__(self):
        return "Пакет обмена " + str(self.type) + " № " + str(self.id)

    class Meta:
        verbose_name = "Пакет обмена"
        verbose_name_plural = "Пакеты обмена"


class Event(models.Model):
    name = models.CharField(max_length=200)
    timestamp = models.DateTimeField('Timestamp', auto_now=True)
    drone = models.ForeignKey(Drone, on_delete=models.SET_NULL, verbose_name="Дрон", blank=True, null=True)
    command = models.ForeignKey(DroneCommand, on_delete=models.SET_NULL, verbose_name="Команда", blank=True, null=True)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, verbose_name="Маршрут", blank=True, null=True)
    drone_plane = models.ForeignKey(DronePlane, on_delete=models.SET_NULL, verbose_name="Взлетная площадка", blank=True,
                                    null=True)
    is_seen = models.BooleanField("Просмотрено", default=False)
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"


class History(models.Model):

    history_timestamp = models.DateTimeField('Timestamp', auto_now=True)
    attitude_roll = models.FloatField("Attitude roll", blank = True, null = True)
    heading = models.FloatField("Heading from North", blank = True, null = True)
    # coordinates_lon_verbose = "Долгота"
    # coordinates_lon_verbose_plural = "Долгота"
    coordinates_lon = models.CharField('Долгота', max_length=200)

    # coordinates_lat_verbose = "Широта"
    # coordinates_lat_verbose_plural = "Широта"
    coordinates_lat = models.CharField('Широта', max_length=200)

    # coordinates_alt_verbose = "Высота"
    # coordinates_alt_verbose_plural = "Высота"
    coordinates_alt = models.CharField('Высота', max_length=200)  # , help_text="help text")

    # air_speed_verbose = "Скорость ветра"
    # air_speed_verbose_plural = "Скорости ветра"
    air_speed = models.CharField('Скорость ветра', max_length=200)

    # ground_speed_verbose = "Скорость движения"
    # ground_speed_verbose_plural = "Скорости движения"
    ground_speed = models.CharField('Скорость движения', max_length=200)

    # is_armable_verbose = "Способен вооружиться"
    # is_armable_verbose_plural = "Способен вооружиться"
    is_armable = models.CharField('Способен вооружиться', max_length=200)

    # is_armed_verbose = "Вооружен"
    # is_armed_verbose_plural = "Вооружен"
    is_armed = models.CharField('Вооружен', max_length=200)

    # status_verbose = "Статус"
    # status_verbose_plural = "Статусы"
    status = models.CharField('Статус', max_length=50)

    # last_heartbeat_verbose = "Последний отклик"
    # last_heartbeat_verbose_plural = "Последние отклики"
    last_heartbeat = models.CharField('Последний отклик', max_length=200)

    # mode_verbose = "Режим"
    # mode_verbose_plural = "Режимы"
    mode = models.CharField('Режим', max_length=50)

    # battery_voltage_verbose = "Напряжение батареи"
    # battery_voltage_verbose_plural = "Напряжения батареи"
    battery_voltage = models.CharField('Напряжение батареи', max_length=200)

    # battery_level_verbose = "Уровень заряда"
    # battery_level_verbose_plural = "Уровни заряда"
    battery_level = models.CharField('Уровень заряда батареи', max_length=5)

    # gps_fixed_verbose = "Спутников"
    # gps_fixed_verbose_plural = "Спутников"
    gps_fixed = models.CharField('Спутников зафиксировано', max_length=5)

    # event_verbose = "Событие"
    # event_verbose_plural = "События"
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, verbose_name="Событие", null=True, blank=True)

    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, default=1, verbose_name="Коптер")

    # drone_plane = models.ForeignKey(DronePlane, on_delete=models.CASCADE, default=1)

    is_uploaded = models.BooleanField("Загружено", default=False)

    connection = models.BooleanField("Соединение", default=False)

    outer_id = models.CharField('Удаленный ID', max_length=200, blank=True, null=True)
    uid = models.CharField('Уникальный идентификатор', max_length=200, blank=True, null=True)

    def __str__(self):
        return "Запись показателей № " + str(self.id)

    class Meta:
        verbose_name = "История"
        verbose_name_plural = "Истории"
    # def __str__(self):
    #     return
