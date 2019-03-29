from django.db import models

class Drone(models.Model):
    name_verbose = "Дрон"
    #name_verbose_plural = "Дроны"
    name = models.CharField(max_length=200, verbose_name=name_verbose)
    connection_ip = models.CharField(max_length=200)
    camera_color_verbose = "Цветная камера"
    camera_color = models.CharField(max_length=200, verbose_name=camera_color_verbose, default="http://")
    camera_thermal_verbose = "Термальная камера"
    camera_thermal = models.CharField(max_length=200, verbose_name=camera_thermal_verbose, default="http://")
    def __str__(self):
        return self.name + '-' + str(self.id)
    class Meta:
        verbose_name = "Дрон"
        verbose_name_plural = "Дроны"
class Event(models.Model):
    event_name = models.CharField(max_length=200)
    def __str__(self):
        return self.event_name
    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
class History(models.Model):
    # outer_id = models.CharField('Outer ID', max_length=200)
    history_timestamp = models.DateTimeField('Timestamp', auto_now=True)

    # coordinates_lon_verbose = "Долгота"
    # coordinates_lon_verbose_plural = "Долгота"
    coordinates_lon = models.CharField('Longitude', max_length=200)

    # coordinates_lat_verbose = "Широта"
    # coordinates_lat_verbose_plural = "Широта"
    coordinates_lat = models.CharField('Latitude', max_length=200)

    # coordinates_alt_verbose = "Высота"
    # coordinates_alt_verbose_plural = "Высота"
    coordinates_alt = models.CharField('Altitude', max_length=200)#, help_text="help text")

    # air_speed_verbose = "Скорость ветра"
    # air_speed_verbose_plural = "Скорости ветра"
    air_speed = models.CharField('Air speed', max_length=200)

    # ground_speed_verbose = "Скорость движения"
    # ground_speed_verbose_plural = "Скорости движения"
    ground_speed = models.CharField('Ground speed', max_length=200)

    # is_armable_verbose = "Способен вооружиться"
    # is_armable_verbose_plural = "Способен вооружиться"
    is_armable = models.CharField('Is armable', max_length=200)

    # is_armed_verbose = "Вооружен"
    # is_armed_verbose_plural = "Вооружен"
    is_armed = models.CharField('Is armed', max_length=200)

    # status_verbose = "Статус"
    # status_verbose_plural = "Статусы"
    status = models.CharField('Status', max_length=50)

    # last_heartbeat_verbose = "Последний отклик"
    # last_heartbeat_verbose_plural = "Последние отклики"
    last_heartbeat = models.CharField('Last heartbeat', max_length=200)

    # mode_verbose = "Режим"
    # mode_verbose_plural = "Режимы"
    mode = models.CharField('Mode', max_length=50)

    # battery_voltage_verbose = "Напряжение батареи"
    # battery_voltage_verbose_plural = "Напряжения батареи"
    battery_voltage = models.CharField('Battery voltage', max_length=200)

    # battery_level_verbose = "Уровень заряда"
    # battery_level_verbose_plural = "Уровни заряда"
    battery_level = models.CharField('Battery level', max_length=5)

    # gps_fixed_verbose = "Спутников"
    # gps_fixed_verbose_plural = "Спутников"
    gps_fixed = models.CharField('GPS fixed', max_length=5)

    # event_verbose = "Событие"
    # event_verbose_plural = "События"
    event = models.ForeignKey(Event, on_delete=models.CASCADE, default=1)

    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, default=1)

    is_uploaded = models.BooleanField("is uploaded", default=False)

    connection = models.BooleanField("is connected", default=False)
    def __str__(self):
        return "Запись показателей № "+str(self.id)
    class Meta:
        verbose_name = "История"
        verbose_name_plural = "Истории"
    # def __str__(self):
    #     return 

