#!/usr/bin/env python

from attention.common_imports import *
from scipy.io import loadmat
import scipy.ndimage.filters as ndfilters

repo_dir = "/Users/sergeyk/work/attention/"
dataset_img_dirs = {
  'where_people_look': opjoin(repo_dir,"external/data/WherePeopleLook/ALLSTIMULI")
}
result_img_dir = opjoin(repo_dir,'results/mturk_viz')
fixmap_dir = opjoin(repo_dir,'results/fixmaps_amt')
# TODO: make relevant methods take argument on command line
if mpi.comm_rank==0:
  ut.makedirs(result_img_dir)
  ut.makedirs(fixmap_dir)

def load_MIT_fixations(force=False):
  """
  Load MIT fixation data for the MIT dataset.
  From .mat file that was output with outputEyeFixationData.m, or
  from a cached DataFrame if it exists.
  """
  df_filename = opjoin(repo_dir,'results/all_fixations_where_people_look.df')
  if not force and opexists(df_filename):
    return DataFrame.load(df_filename)
  mat_filename = opjoin(repo_dir,'results/all_fixations_where_people_look.mat')
  mat_data = loadmat(mat_filename)['celldata']
  images = [x.strip() for x in open('where_people_look.txt').readlines()]
  worker_ids = ['CNG', 'ajs', 'emb', 'ems', 'ff', 'hp', 'jcw', 'jw', 'kae', 'krl', 'po', 'tmj', 'tu', 'ya', 'zb']
  all_data = []
  image_sizes = {}
  for i in range(len(images)):
    print("%d/%d"%(i,len(images)))
    img = imread(opjoin(dataset_img_dirs['where_people_look'],images[i]))
    image_sizes[images[i]] = img.shape
    for w in range(len(worker_ids)):
      data = {}
      data['worker_id'] = worker_ids[w]
      locs = mat_data[i,w]
      locs -= 1 # compensate for MATLAB's 1-based indexing
      locs = locs[(locs[:,0]>=0) & (locs[:,1]>=0)]
      data['history'] = {'x':locs[:,0].tolist(),'y':locs[:,1].tolist()}
      data['img'] = images[i]
      data['dataset'] = "where_people_look_MIT"
      data['img_width'] = image_sizes[images[i]][1]
      data['img_height'] = image_sizes[images[i]][0]
      all_data.append(data)
  df = DataFrame(all_data)
  df.save(df_filename)
  return df

def load_MTurk_results(json_filename):
  """
  Load MTurk result data from a json file that is populated by hits.rb review.
  """
  # Assemble a list of dictionaries, one for each assignment
  lines = open(json_filename).readlines()
  all_assignments = []
  failed = 0
  for line in lines:
    try:
      assignment_data = json.loads(line)
      # The history object is doubly encoded as JSON
      history = json.loads(assignment_data['history'])
      assignment_data['history'] = history
      all_assignments.append(assignment_data)
    except Exception as e:
      failed += 1
      print("Could not load data for a HIT assignment:")
      print(e)
  # Construct a DataFrame from the list of dictionaries, and drop
  # duplicates.
  print("%d failed"%failed)
  df = DataFrame(all_assignments)
  df.pop('Submit')
  df = df.drop_duplicates(['assignment_id','worker_id'])
  return df

def select(all_data,img=None,task=None,worker_id=None):
  """
  Fetch all data that exists for a given image, task, and worker_id.
  """
  data = all_data
  if img:
    data = data[all_data['img']==img]
  if task:
    data = data[all_data['task']==task]
  if worker_id:
    data = data[all_data['worker_id']==worker_id]
  return data

def visualize_fixations(data):
  "Display the history of fixations on the image in the assignment data."
  img = load_image(data['img']) #TODO: pass in dataset as well
  if not (isinstance(data['history'],list) or isinstance(data['history'],dict)):
    print("history not a list, skipping")
    return
  try:
    fixations = DataFrame(data['history'])
  except:
    print("not working out, returning")
    return
  if fixations.shape[0] < 1:
    print("Not enough fixations!")
    return
  # rescale fixations
  if 'img_width' in data.index:
    fixations.x *= img.shape[1]/float(data['img_width'])
    fixations.y *= img.shape[0]/float(data['img_height'])
  labels = [str(i) for i in range(fixations.shape[0])]
  imshow(img)
  plt.plot(fixations.x,fixations.y,'ro')
  for label,x,y in zip(labels,fixations.x,fixations.y):
    plt.annotate(label,xy=(x,y),
      xytext = (-2, -4), textcoords = 'offset points',
      bbox = dict(boxstyle = 'round,pad=0.2', fc = 'yellow', alpha = 0.5))
  print("%(dataset)s: %(img)s"%data)
  print(data['worker_id'])
  try:
    print(data['task'])
    print(data['user_content'])
  except:
    pass

  plt.savefig(opjoin(result_img_dir,"%(img)s_%(worker_id)s.png"%data))

def construct_all_attention_maps(df):
  imgs = np.unique(df['img'].tolist())
  for img in imgs:
    img_df = df[df['img']==img]
    # setting sigma extra high for the amt set!
    [(construct_attention_map(df[df.img==img],'top_%d'%k,k,sigma=32)) for k in [1,4,8,16]]

def construct_attention_map(df,suffix='default',top_k=4,sigma=24):
  """
  Output fixation points and map images for the given df.
  Will concatenate all data in the df. Expects only one image in the df.
  """
  imgs = np.unique(df['img'].tolist())
  assert(len(imgs)==1)
  img = imgs[0]
  all_fixations = DataFrame(None,columns=['x','y'])
  for h in df.history:
    try:
      if top_k > 0:
        all_fixations = all_fixations.append(DataFrame(h).ix[1:top_k+1],True)
      else:
        all_fixations = all_fixations.append(DataFrame(h).ix[1:],True)
    except:
      print("oooops, something went wrong in construct_attention_map")
  shape = df.ix[df.index[0]][['img_height','img_width']].astype(int)
  fixpts = np.zeros(shape)
  inds = all_fixations[['y','x']].values.astype(int)
  fixpts[inds[:,0],inds[:,1]] = 100 # for numerical stability in the convolution below

  # Now blur with a Gaussian
  f = ndfilters.gaussian_filter(fixpts,sigma)
  fixmap = f / f.max()

  # Save
  filename = opjoin(fixmap_dir,'%s_%s.jpg'%(img,suffix))
  imsave(filename,fixmap)

  return fixmap

def figure_out_fixation_maps(df_mit,
    img='i05june05_static_street_boston_p1010764.jpeg'):
  "Figure out the params that match Judd's fixation maps."
  # Load Judd's version
  basename,_ = os.path.splitext(img)
  fixmap = imread(opjoin(repo_dir,'external/data/WherePeopleLook/ALLFIXATIONMAPS/%s_fixMap.jpg'%basename))
  fixpts = imread(opjoin(repo_dir,'external/data/WherePeopleLook/ALLFIXATIONMAPS/%s_fixPts.jpg'%basename))
  # get rid of JPG compression artifacts
  fixpts[fixpts<200] = 0
  fixpts[fixpts>200] = 1

  img_df = df_mit[df_mit['img']==img]
  top_k = 4 # figured out that it is 4, which contradicts paper's claim of 6
  sigma = 24 # figured this out with a simple grid search.
  # overall abs difference pixel error is 233K for these settings on the first image.
  fixpts,fixmap = construct_attention_map(img_df,top_k,sigma=22)

  # Figure out the parameters, with code I deleted :)
  # It doens't really matter, the parameters can't make a big difference
  # and I will be changing them anyway.

def load_image(img_name,dataset=None):
  "Load the image of given name."
  if not dataset:
    dataset = 'where_people_look'
  filename = opjoin(dataset_img_dirs[dataset],img_name)
  img = imread(filename)
  return img

def plot_discrete(vals,top_K=10):
  "Plot a bar chart of the histogram of the discrete values in colname."
  if isinstance(vals,np.ndarray):
    vals = vals.tolist()
  uvals = set(vals)
  counts = [vals.count(val) for val in uvals]
  # TODO: sort by occurrence, and only display top K
  fig = plt.figure()
  ax = fig.add_subplot(111)
  ax.bar(range(len(counts)), counts, align='center')
  ax.set_ylabel('Count')
  ax.set_xticks(range(len(counts)))
  ax.set_xticklabels(list(uvals))
  fig.autofmt_xdate()
  plt.show()

def amt_stats(df):
  "Output some stats about the given AMT dataset."
  def hist_helper(series,thing,group):
    plt.clf()
    series.hist(bins=np.arange(series.max()+2))
    plt.xlabel('# of %s per %s'%(thing, group))
    plt.ylabel('frequency')
    plt.show()

  s = {}
  def print_and_save(k,v):
    print("%s: %s"%(k,str(v)))
    s[k] = v

  print_and_save('total_num_assignments', df.shape[0])

  # Group by worker
  grouped = df.groupby('worker_id')
  print_and_save('num_workers', len(grouped.groups))
  hist_helper(grouped['img'].nunique(), 'images','worker')
  hist_helper(grouped['task'].nunique(), 'task types','worker')

  # Group by img
  grouped = df.groupby('img')
  print_and_save('num_images', len(grouped.groups))
  hist_helper(grouped['worker_id'].nunique(), 'workers','img')
  hist_helper(grouped['task'].nunique(), 'task types','img')

  # output json file of {img: {task: #assignments}}
  def unique_count_dict(series):
    d = {'describe':0, 'count_people':0, 'text':0}
    for s in series:
      d[s] += 1
    return d
  data = [unique_count_dict(group['task']) for _,group in grouped]
  with open('amt_per_task_counts.json','w') as f:
    json.dump(data,f)

  with open('amt_counts.json','w') as f:
    json.dump(dict(grouped.size()),f)

def visualize_fixations_on_dataset(df,show=True):
  """
  Plot fixations on each image, for each user, and output to files.
  Optionally, plot to screen, pausing for key presses in between.
  """
  for i in df.index:
      visualize_fixations(df.ix[i])
      if show:
        plt.show()
        raw_input()

def load_face_features(img):
  "Process the JSON files output by the Face.com detection API into Face likelihood maps."
  None

def load_features(img):
  """
  Load MIT features for the given img filename.

  # FEATURES(:, 1:13) = findSubbandFeatures(img, dims);
  # FEATURES(:, 14:16) = findIttiFeatures(img, dims);
  # FEATURES(:, 17:27) = findColorFeatures(img, dims);
  # FEATURES(:, 28) = findTorralbaSaliency(img, dims);
  """
  feats_dir = '/Users/sergeyk/work/attention/results/mit_feats'
  feats_filename = opjoin(feats_dir,'%s_mit_feats.mat'%img)
  feats = loadmat(feats_filename)['FEATURES']
  return feats

if __name__ == '__main__':
  if False:
    df_mit = load_MIT_fixations()
    visualize_fixations_on_dataset(df_mit)

  df_amt = load_MTurk_results(sys.argv[1])
  #amt_stats(df_amt)
  #visualize_fixations_on_dataset(df_mit)