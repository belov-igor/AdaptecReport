import subprocess
import pandas as pd
import pretty_html_table

from config.hosts import WINDOWS_HOSTS, LINUX_HOSTS  # хосты из файла, разделены на списки windows и linux
from config.hosts import WINDOWS_USER, LINUX_USER    # пользователи взяты из файла, разделены на windows и linux
from scripts.send_email import ReportSender


class AdaptecReport:

    def __init__(self, username, hostname):
        self.arconf_path = str()
        self.df = None
        self.table = None
        self.username = username
        self.hostname = hostname
        self.config = dict()
        self.device_name = str()
        self.device_status = str()
        self.data = str()

    def adaptec_counter(self, arconf_path):
        """
        Функция подсчета количества используемых adaptec
        :arconf_path: путь до утилиты arcconf
        :return: количество используемых adaptec
        """
        self.arconf_path = arconf_path
        count = 0

        # Подключение к хостам по ssh, получение данных arcconf getversion
        connect = subprocess.run(
            ["ssh", f"{self.username}@{self.hostname}", f"{self.arconf_path}", "getversion"],
            stdout=subprocess.PIPE)
        data = connect.stdout.decode().split('\n')
        for string in data:
            if 'controllers found' in string.lower():
                count = int(string.split(':')[-1])
        return count

    def logical_device_status(self):
        """
        Подключение к хостам по ssh, получение и обработка отчета adaptec arcconf по логическим дискам.
        :return: сonfig - обработанные данные с arcconf ld в виде словаря.
        """
        # По умолчанию arcconf должен быть добавлен на сервере в переменную PATH
        arcconf_path = 'arcconf'

        # В esxi arcconf в PATH не добавлен, лежит в собственных datavol или ssdvol (унифицировать, к сожалению, нельзя)
        if 'esxi' in self.hostname:
            arcconf_path = f'/vmfs/volumes/{self.hostname}_ssdvol/arcconf'

        # Подсчет количества используемых adaptec'ов
        adaptec_count = self.adaptec_counter(arconf_path=arcconf_path)

        # Подключение к хостам по ssh, получение данных arcconf, парсинг
        for adaptec in range(1, adaptec_count + 1):
            connect = subprocess.run(
                ["ssh", f"{self.username}@{self.hostname}", f"{arcconf_path}", "GETCONFIG", f"{adaptec}", "ld"],
                stdout=subprocess.PIPE)
            self.data = connect.stdout.decode().split('\n')
            for string in self.data:
                if 'device name' in string.lower():
                    self.device_name = string.split()[-1]
                if 'status of logical device' in string.lower():
                    self.device_status = string.split()[-1]
                self.config.update({self.device_name: self.device_status})

    def run(self):
        self.logical_device_status()
        return self.config


def get_data_frame(data):
    """
    Формирование html-таблицы
    :param data: данные в виде словаря
    :return: данные, сформированные в html-таблицу
    """
    df = pd.DataFrame.from_dict(data=data, orient='index')
    table = pretty_html_table.build_table(df=df, color='blue_light', index=True,
                                          text_align='center', padding="0px 5px 0px 5px")
    return table


if __name__ == '__main__':

    adaptec_report = dict()
    hosts_dict = dict()

    try:
        # Формирование словаря со списком хостов, где ключ - имя пользователя
        hosts_dict.update({LINUX_USER: LINUX_HOSTS,
                           WINDOWS_USER: WINDOWS_HOSTS})

        # Проход по хостам и формирование отчета в виде html-таблицы
        for user_name, hosts in hosts_dict.items():
            for host in hosts:
                report = AdaptecReport(username=user_name, hostname=host)
                ld_stat = report.run()
                adaptec_report.update({host: ld_stat})
        report_table = f'<h2>Adaptec report</h2>\n' \
                       f'{get_data_frame(data=adaptec_report)}'
    except Exception as error:
        report_table = error
    else:
        # Отправка отчета
        report_message = ReportSender(subject='Adaptec report',
                                      body=report_table)
        report_message.run()
