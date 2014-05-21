#!/usr/bin/env python
"""
Process a directory containing images to output blurred versions of all images.
Does not re-output blurred images.
Also uploads the images to S3.
"""
from glob import glob
import boto
import skimage
from skimage.io import imread,imshow,imsave
from attention.common_imports import *

def upload_to_s3(filename,bucket,force=True):
  k = boto.s3.key.Key(bucket)
  k.key = os.path.basename(filename)
  if force or not k.exists():
    k.set_contents_from_filename(filename)
    k.set_acl('public-read')
    print("Uploaded %s to s3"%filename)

data_dir = os.path.expanduser("~/work/attention/external/data/WherePeopleLook/ALLSTIMULI/")
data_dir = "./images/"

all_jpegs = set(glob(data_dir+'*.jpeg'))
blur_jpegs = set(glob(data_dir+'*_blur*.jpeg'))
unblurred_jpegs = list(all_jpegs.difference(blur_jpegs))

# establish boto connection
conn = boto.connect_s3()
bucket = conn.get_bucket('where_people_look')
bucket.set_acl('public-read')

blurs = [2,4,8]
for i in range(comm_rank,len(unblurred_jpegs),comm_size):
  jpeg = unblurred_jpegs[i]
  upload_to_s3(jpeg,bucket)
  for blur in blurs:
    # check if local blured copy exists
    blur_name = jpeg+'_blur%(blur)d.jpeg'%locals()
    if not os.path.exists(blur_name):
      os.system("convert %(jpeg)s -gaussian-blur 0x%(blur)d %(blur_name)s"%locals())
      print("finished blur %(blur)d on %(jpeg)s"%locals())
    
    # check if S3 copy exists and upload if it does not
    upload_to_s3(blur_name,bucket)
