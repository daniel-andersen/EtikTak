# encoding: utf-8

# Copyright (c) 2012, Daniel Andersen (dani_ande@yahoo.dk)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import uuid

from etiktak.util import util

from django.db import models

class SmsVerificationManager(models.Manager):
    def verify_user(self, mobile_number, password, challenge):
        verifications = self.filter(mobile_number_hash=util.sha256(mobile_number))
        if verifications is None or len(verifications) == 0:
            raise BaseException("No challenge found for mobile number: %s" % mobile_number)
        verification = verifications[0]
        if not verification.challenge_hash == util.sha256(challenge):
            raise BaseException("Provided challenge for mobile number %s doesn't match" % mobile_number)
        clients = Client.objects.filter(mobile_number_hash_password_hash_hashed=util.sha256(util.sha256(mobile_number) + util.sha256(password)))
        if clients is None or len(clients) == 0:
            raise BaseException("No client found for mobile number: %s" % mobile_number)
        client = clients[0]
        client.verified = True
        client.save()

class ClientManager(models.Manager):
    def get(self, mobile_number, password):
        clients = self.filter(mobile_number_hash_password_hash_hashed=util.sha256(util.sha256(mobile_number) + util.sha256(password)))
        return clients[0]

class Client(models.Model):
    uid = models.CharField(max_length=255, unique=True) # EncryptedCharField(max_length=255)
    mobile_number_hash_password_hash_hashed = models.CharField(max_length=255, unique=True) # EncryptedCharField(max_length=255)
    verified = models.BooleanField(default=False)
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    objects = ClientManager()

    @staticmethod
    def create_client_key(mobile_number, password):
        """
        Creates and saves a client key with autogenerated UID and with a hash of
        the sum of the specified mobile number hashed concatenated with the specified
        password hashed.
        """
        client_key = Client(
            uid = uuid.uuid4(),
            mobile_number_hash_password_hash_hashed = util.sha256(util.sha256(mobile_number) + util.sha256(password)))
        client_key.save()
        return client_key

    def __unicode__(self):
        return u"%s | %s" % (self.uid, self.mobile_number_hash_password_hash_hashed)

    class Meta:
        verbose_name = u"Klientnøgle"
        verbose_name_plural = u"Klientnøgler"


class SmsVerification(models.Model):
    challenge_hash = models.CharField(max_length=255) # EncryptedCharField(max_length=255)
    mobile_number_hash = models.CharField(max_length=255, unique=True) # EncryptedCharField(max_length=255)
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    objects = SmsVerificationManager()

    @staticmethod
    def create_challenge(mobile_number):
        """
        Creates and saves a SMS verification with autogenerated challenge
        """
        sms_verification = SmsVerification(
            challenge_hash = util.sha256(util.generate_challenge()),
            mobile_number_hash = util.sha256(mobile_number))
        sms_verification.save()
        return sms_verification

    def __unicode__(self):
        return u"%s | %s | %s" % (self.challenge_hash, self.mobile_number_hash, self.verified)

    class Meta:
        verbose_name = u"SMS verifikation"
        verbose_name_plural = u"SMS verifikationer"
