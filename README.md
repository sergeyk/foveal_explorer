Foveal Explorer
===
See a [short blog post](http://sergeykarayev.com/foveal-explorer/) for more info.

**NOTE**: this code was used in an abandoned research project, and is released only to demonstrate the Foveal Explorer JavaScript applet, and host the gathered AMT fixation data, without any support.

---

### Viewing the task page locally.

    python -m SimpleHTTPServer
    open http://0.0.0.0:8000

### Loading data gathered on AMT

Before abandoning the project, I gathered 10K HITs (human intelligence tasks) on Amazon Mechanical Turk, equally distributed between three tasks (describe scene, count people, find all text), on the MIT Attention dataset.

```python
In [1]: import pandas

In [2]: df = pandas.read_pickle('dataframe_2012-05.pickle')

In [3]: df.head()
Out[3]:
        worker_id                                           img img_height  \
0  A2J2P9JE374XCM       istatic_hotel_room_indoor_IMG_0999.jpeg        818
1  A323WW03VM8089       istatic_hotel_room_indoor_IMG_0999.jpeg        818
2   AP5CXT3G9EIBH       istatic_hotel_room_indoor_IMG_0999.jpeg        818
3  A2WZJC3N97GJ9Z  i05june05_static_street_boston_p1010764.jpeg        614
4  A1E3WL1MAZS6KC  i05june05_static_street_boston_p1010800.jpeg        614

  img_width          task                                       user_content  \
0       614      describe                                           a toilet
1       614  count_people                                                  0
2       614  count_people                                                  0
3       819      describe  A large number of cars are parked on the left ...
4       819          text                                               none

  comment                                            history
0          [{u'y': 408, u'x': 305, u'frameCount': 94, u't...
1          [{u'y': 415, u'x': 306, u'frameCount': 42, u't...
2          [{u'y': 411, u'x': 314, u'frameCount': 59, u't...
3          [{u'y': 308, u'x': 409, u'frameCount': 59, u't...
4          [{u'y': 309, u'x': 409, u'frameCount': 33, u't...

[5 rows x 8 columns]
```

### Dataset

We use the [Where humans look](http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html) dataset.

### Creating blurred images

    find ^*blur*.jpeg -exec convert -gaussian-blur 0x1.414 {} {}_blur2.jpeg \;
    find *blur2.jpeg -exec convert -gaussian-blur 0x1.414 {} {}_blur4.jpeg \;
    find *blur4.jpeg -exec convert -gaussian-blur 0x1.414 {} {}_blur8.jpeg \;
