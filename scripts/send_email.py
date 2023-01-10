import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# информация о почтовом сервере, кто отправляет и кому, подтягивается из файла
from config.email_server import SMTP_SERVER, FROM, TO


class ReportSender:
    """
    Отправка MIME-сообщений в формате HTML на почтовый сервер
    """
    def __init__(self, subject, body):
        self.body = body
        self.subject = subject
        self.message = None
        self.main_table = None
        self.msg = None
        self.server = None
        self.df = None

    def smtp_connect(self):
        """
        Подключение к SMTP серверу
        """
        self.server = smtplib.SMTP(SMTP_SERVER)

    def create_message(self):
        """
        Формирование сообщения MIME-типа
        """
        self.msg = MIMEMultipart('alternative')
        self.msg['Subject'] = self.subject
        self.msg['From'] = FROM
        self.msg['To'] = TO
        self.body = MIMEText(self.body, 'html')
        self.msg.attach(self.body)

    def send_message(self, message):
        """
        Отправка
        """
        self.message = message
        self.server.send_message(msg=self.msg)

    def run(self):
        self.smtp_connect()
        self.create_message()
        self.send_message(self.msg)
        self.server.quit()
