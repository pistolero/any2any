# -*- coding: utf-8 -*-
from django.db.models import ForeignKey, CharField, Model, ManyToManyField, PositiveIntegerField, IntegerField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Journal(Model):
    name = CharField(max_length=100)

    def __unicode__(self):
        return self.name

class Person (Model):
    firstname = CharField(max_length=100)
    lastname = CharField(max_length=100)

class Author (Person) :
    nickname = CharField(max_length=100)

class Journalist(Author):
    journal = ForeignKey(Journal)

class Columnist(Journalist):
    column = CharField(max_length=100)

class Book (Model) :
    author = ForeignKey(Author, null=True)
    title = CharField(max_length=100)
    comments = CharField(max_length=100)

class Dish (Model) :
    name = CharField(max_length=100)

class Gourmand (Person) :
    pseudo = CharField(max_length=100)
    favourite_dishes = ManyToManyField(Dish)

    def __unicode__(self):
        return self.pseudo

class WritingSausage(Author, Dish):
    greasiness = IntegerField()

class Bookmark(Model):
    name = CharField(max_length=100)
    content_type = ForeignKey(ContentType)
    object_id = PositiveIntegerField()
    to = generic.GenericForeignKey('content_type', 'object_id')
