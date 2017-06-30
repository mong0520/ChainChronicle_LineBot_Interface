# -*- coding: utf-8 -*-
import flickr_api

# FIRST time
#a = flickr_api.auth.AuthHandler() #creates the AuthHandler object
#perms = "write" # set the required permissions
#url = a.get_authorization_url(perms)
#print url
#ans = raw_input("Please enter your pin code: ")
#a.set_verifier(ans)
#flickr_api.set_auth_handler(a)
#.save('myauth')
#

# if you already have the token file
flickr_username = 'Neil.Wei'
flickr_api.set_keys(api_key='5d3fd4c39ad5005fb9547fc540647cf9', api_secret='83d46646050639ab')
auth_handler = flickr_api.auth.AuthHandler()
a = auth_handler.load('myauth')
flickr_api.set_auth_handler(a)
user = flickr_api.Person.findByUserName(flickr_username)
#

def upload_image(img_path, title='Uploaded by Line Bot', photo_set='LineBot'):
    photo = flickr_api.upload(photo_file=img_path, title=title)
    print photo
    if get_photoset(photo_set) is None:
        print 'Create photoset {0}'.format(photo_set)
        create_photoset(photo_set, photo)
    else:
        print 'Add photo to {0}'.format(photo_set) 
        ps = get_photoset(photo_set)
        ps.addPhoto(photo=photo)


def get_all_photosets():
    if flickr_username is None:
        return None
    photosets = user.getPhotosets()
    return photosets


def create_photoset(title, primary_photo):
    photoset = flickr_api.Photoset.create(title=title, primary_photo=primary_photo)
    return photoset


def get_photoset(title):
    photosets = get_all_photosets()
    for ps in photosets:
        if title == ps.title:
            return ps
    return None

if __name__ == '__main__':
    #get_all_photosets()
    #ps = get_photoset(title='Liz')
    #print ps
    upload_image('img/pic-1.jpg')


