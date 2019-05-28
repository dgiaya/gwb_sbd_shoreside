
import datetime
import email
import os
import imaplib
from time import sleep
from threading import Thread
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

class EmailSniffer():

    def __init__(self,
                 email_account,
                 username=None, pw=None,
                 check_rate_min=1,
                 imap_svr=None, imap_port=None,
                 smtp_svr=None, smtp_port=None,
                 subject_line_filt=None,
                 arrival_email_filt=None,
                 attachment_ext_filt=None):
        self.SUBJECT = subject_line_filt
        self.SENDER = arrival_email_filt
        self.FROM = email_account
        self.email_username = username
        self.email_pw = pw
        self.email_check_rate = check_rate_min
        self.email_incoming_svr = imap_svr
        self.email_outgoing_svr = smtp_svr
        self.email_incoming_port = imap_port
        self.email_outgoing_port = smtp_port
        self.attachment_ext_filt = attachment_ext_filt

        self.incoming_attachment_queues = []

        self.last_read = datetime.datetime.now()
        self.alive = True

        self._threadL = Thread(target=self._listen)
        self._threadL.setDaemon(True)
        self._threadL.start()

    def _listen(self):
        print('Listen thread started')
        while self.alive:
            date = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%d-%b-%Y")

            M = imaplib.IMAP4(self.email_incoming_svr)

            response, details = M.login(self.email_username, self.email_pw)
            M.select('INBOX')

            print('Checking INBOX')
            #Search for messages in the past hour with subject line specified and from sender specified
            response, items = M.search(None,
                                       '(UNSEEN SENTSINCE {date} HEADER Subject "{subject}" FROM "{sender}")'.format(
                                           date=date,
                                           subject=self.SUBJECT,
                                           sender=self.SENDER
                                       ))

            for emailid in items[0].split():
                response, data = M.fetch(emailid, '(RFC822)')

                mail = email.message_from_string((data[0][1]).decode('utf-8'))

                if not mail.is_multipart():
                    continue
                for part in mail.walk():
                    if part.is_multipart():
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    file_nm = part.get_filename()
                    if file_nm is None:
                        continue
                    filename, fileext = os.path.splitext(file_nm)
                    if self.attachment_ext_filt is not None:
                        if fileext != self.attachment_ext_filt:
                            continue
                    msg = part.get_payload(decode=True)

                    print('Found msg in INBOX')
                    print(msg)
                    for q in self.incoming_attachment_queues:
                        q.put_nowait(msg)


                    temp = M.store(emailid, '+FLAGS', '\\Seen')

            M.close()
            M.logout()
            sleep(self.email_check_rate * 60)

    def write(self, msg):
        print('Writing e-mail')
        email_msg = MIMEMultipart()
        email_msg['Subject'] = "{0}".format(self.SUBJECT)
        email_msg['To'] = self.SENDER
        email_msg['From'] = self.FROM

        part = MIMEText(msg.hex())
        email_msg.attach(part)

        attachment = MIMEApplication(msg)

        attachment.add_header('Content-Disposition', 'attachment',
                              filename="{0}.{1}".format((datetime.datetime.utcnow()).strftime("%d%b%YT%H%M%S%z"),
                                                        self.attachment_ext_filt))
        email_msg.attach(attachment)
        print('SMTP connect')
        print(self.email_outgoing_svr)
        print(self.email_outgoing_port)
        smtp = smtplib.SMTP()
        smtp.connect(self.email_outgoing_svr)
        print('SMTP send')
        smtp.sendmail(self.FROM, [email_msg['To'], self.FROM], email_msg.as_string())
        print('SMTP quit')
        smtp.quit()

    def close(self):
        self.alive = False

    def append_incoming_attachment_queue(self, queue_to_append):
        self.incoming_attachment_queues.append(queue_to_append)
