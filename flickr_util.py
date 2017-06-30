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
flickr_api.set_keys(api_key='5d3fd4c39ad5005fb9547fc540647cf9', api_secret='83d46646050639ab')
auth_handler = flickr_api.auth.AuthHandler()
a = auth_handler.load('myauth')
flickr_api.set_auth_handler(a)
#

def upload_image(img_path, title='AutoUpload', photo_set):
    flickr_api.upload(photo_file=img_path, title=title)
