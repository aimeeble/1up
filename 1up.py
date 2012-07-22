from twilio.rest import TwilioRestClient
import time
import smtplib
from email.mime.text import MIMEText
import json
import sys


class InvalidConfig(Exception):
   def __init__(self, field_name):
      super(InvalidConfig, self).__init__("Invalid config: missing %s" % field_name)


class Config(object):
   '''Loads a JSON config file and presents its keys as if they were ours.

   '''

   def __init__(self, config_file):
      with open(config_file, 'r') as fh:
         self.values = json.load(fh)
      self._validate()

   def _validate(self):
      '''Checks for required keys in the config dict.

      '''

      if "from" not in self.values:
         raise InvalidConfig("from")
      if "email" not in self.values["from"]:
         raise InvalidConfig("from/email")
      if "sms" not in self.values["from"]:
         raise InvalidConfig("from/sms")

      if "twillio" not in self.values:
         raise InvalidConfig("twillio")
      if "acct" not in self.values["twillio"]:
         raise InvalidConfig("twillio/acct")
      if not self.values["twillio"]["acct"]:
         raise InvalidConfig("twillio/acct")
      if "token" not in self.values["twillio"]:
         raise InvalidConfig("twillio/token")
      if not self.values["twillio"]["token"]:
         raise InvalidConfig("twillio/token")

      if "smtp" not in self.values:
         raise InvalidConfig("smtp")
      if "server" not in self.values["smtp"]:
         raise InvalidConfig("smtp/server")
      if "user" not in self.values["smtp"]:
         raise InvalidConfig("smtp/user")
      if not self.values["smtp"]["user"]:
         raise InvalidConfig("smtp/user")
      if "pass" not in self.values["smtp"]:
         raise InvalidConfig("smtp/pass")
      if not self.values["smtp"]["pass"]:
         raise InvalidConfig("smtp/pass")

   def __getitem__(self, key):
      '''Gets an item from our settings values.

      '''
      return self.values[key]


class ExtraLife(object):
   '''Sends a bunch of coin SMSs then sends a 1-up email.

   Note: for this to be amusing at all, the receipient must have a set of
   ringtones on their phone such that SMS messages cause a Mario coin sound,
   and email cause a 1-up sound.

   This will send the specified number of coins to the SMS address, and then
   send a final email at the end.  Events are separated by the coin and final
   delay values.
   '''

   def __init__(self, email_addr, sms_addr, coin_count, coin_delay=2, final_delay=10, config_file='config.json'):
      '''Initializes the object and loads the configuration file.

      This will throw if the config file is missing or incomplete.
      '''

      self.email_addr = email_addr
      self.sms_addr = sms_addr
      self.coin_count = coin_count
      self.coin_delay = coin_delay
      self.final_delay = final_delay

      self.config = Config(config_file)

      if len(self.sms_addr) != 12 or self.sms_addr[0] != "+" or self.sms_addr[1] != "1" :
         raise Exception("invalid SMS address: %s" % self.sms_addr)

      self.client = TwilioRestClient(self.config["twillio"]["acct"],
                                     self.config["twillio"]["token"])

   def _send_sms_coins(self):
      '''Sends a pre-specified number of SMS messages to the same number.

      This will delay between each message. Ideally, the delay is large enough
      so that each message triggers a distinct notification sound.
      '''

      print "Sending %d coins..." % self.coin_count
      for i in range(0, self.coin_count):
         print "Sending coin %d!" % i
         msg = self.client.sms.messages.create(
               to=self.sms_addr,
               from_=self.config["from"]["sms"],
               body="Coin %s!" % i)
         time.sleep(self.coin_delay)

   def _send_email_1up(self):
      '''Sends a final email message.

      The email message should be sent sufficiently after all the coins. If it
      arrives before the final coin, all the fun is ruined! :P
      '''

      msg = MIMEText("""
Wow, that's a lot of coins you just got!

Though, because SMS sucks*, it wasn't quite 100 (only %(coin_count)d). So, I'm just going to assume you've received %(coins_left)d 'coins' earlier today through normal converstations :-)

*I timed it out and at a reasonable delay so that each notification is distinct, your phone would be beeping for something like 10 minutes... and I didn't want to completely drain your battery!

-Aimee
""" % {
            "coin_count": self.coin_count,
            "coins_left": 100 - self.coin_count
         })
      msg["Subject"] = "1up!"
      msg["From"] = self.config["from"]["email"]
      msg["To"] = self.email_addr

      s = smtplib.SMTP_SSL(*self.config["smtp"]["server"])
      s.login(self.config["smtp"]["user"], self.config["smtp"]["pass"])

      print "Sending 1-up"
      s.sendmail(self.config["from"]["email"], [self.email_addr], msg.as_string())
      s.quit()

   def run(self):
      self._send_sms_coins()
      print "Sleeping %us before sending 1up" % self.final_delay
      time.sleep(self.final_delay)
      self._send_email_1up()


if __name__ == "__main__":
   if len(sys.argv) < 3:
      print "%s sms email [coins=10]" % (sys.argv[0])
      print "\tsms   -- number to SMS, in the form +1NNNNNNNNNN"
      print "\temail -- email address to send final notification to"
      print "\tcoins -- number of coins to send, defaults to 10"
      sys.exit(1)

   count = 10
   if len(sys.argv) > 3:
      count = int(sys.argv[3])

   try:
      life = ExtraLife(sys.argv[2], sys.argv[1], count)
   except IOError, e:
      print "Failed to load config file: %s" % (e)
   except ValueError, e:
      print "Invalid JSON in config file: %s" % (e)
   except InvalidConfig, e:
      print "Missing required key in config file: %s" % (e)
   else:
      life.run()
