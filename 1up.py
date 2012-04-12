from twilio.rest import TwilioRestClient
import time
import smtplib
from email.mime.text import MIMEText
try:
   from config import *
except:
   raise Exception("Make a config.py file!")

class ExtraLife(object):
   def __init__(self, email_addr, sms_addr, coin_count, coin_delay = 2, final_delay = 10):
      self.email_addr = email_addr
      self.sms_addr = sms_addr
      self.coin_count = coin_count
      self.coin_delay = coin_delay
      self.final_delay = final_delay

      if self.sms_addr[0] != "+" or self.sms_addr[1] != "1" or len(self.sms_addr) != 12:
         raise Exception("invalid SMS address: %s" % self.sms_addr)

      self.client = TwilioRestClient(ACCT, TOKEN)

   def send_sms_coins(self):
      print "Sending %d coins..." % self.coin_count
      for i in range(0, self.coin_count):
         print "Sending coin %d!" % i
         msg = self.client.sms.messages.create(to=self.sms_addr,
               from_=FROM_SMS, body="Coin %s!" % i)
         time.sleep(self.coin_delay)

   def send_1up_email(self):
      msg = MIMEText("""
Wow, that's a lot of coins you just got!

Though, because SMS sucks*, it wasn't quite 100 (only %(coin_count)d).  So, I'm
just going to assume you've received %(coins_left)d 'coins' earlier today through normal
converstations :-)


*I timed it out and at a reasonable delay so that each notification is
distinct, your phone would be beeping for something like 10 minutes... and I
didn't want to completely drain your battery!

-Aimee
""" % {
   "coin_count": self.coin_count,
   "coins_left": 100 - self.coin_count
})
      msg["Subject"] = "1up!"
      msg["From"] = FROM_EMAIL
      msg["To"] = self.email_addr

      s = smtplib.SMTP_SSL(*SMTP_SERVER)
      s.login(SMTP_USER, SMTP_PASS)

      print "Sending 1-up"
      s.sendmail(FROM_EMAIL, [self.email_addr], msg.as_string())
      s.quit()

   def run(self):
      self.send_sms_coins()
      time.sleep(self.final_delay)
      self.send_1up_email()

if __name__ == "__main__":
   life = ExtraLife("EMAIL", "SMS", 10)
   life.run()
