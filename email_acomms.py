from email_sniffer import EmailSniffer
from gwb_modem import GWBModem
from queue import Queue
from credentials import *


email = EmailSniffer(
    email_account=EMAIL_ACCOUNT,
    username=USERNAME,
    pw=PW,
    check_rate_min=1,
    imap_svr=IMAP_SVR,
    imap_port=IMAP_PORT,
    smtp_svr=SMTP_SVR,
    smtp_port=SMTP_PORT,
    imei='300234065063620',
    arrival_email_filt= 'dgiaya@whoi.edu',
    attachment_ext_filt='.sbd'
)

modem = GWBModem(name = 'gwbmodem', log_path='./', log_level='INFO')
modem.connect_serial(port='/dev/ttyUSB0', baudrate=19200)

xmitqueue = Queue()

modem.packet_listeners.append(email.write)
email.append_incoming_attachment_queue(xmitqueue)

while 1:
    msg = xmitqueue.get()
    if msg is not None:
        modem.send_packet_data(0, msg)