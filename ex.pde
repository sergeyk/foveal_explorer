interface JavaScript {
  void recordData(float x, float y, float time, int frameCount);
}

JavaScript javascript;
void bindJavascript(JavaScript js) {
  javascript = js;
}
int img_width() {
  return width;
}

// Constants
float doubling_radius = 80;
float num_levels = 3;
int max_radius = doubling_radius*num_levels;
int diameter = 2*max_radius;

float csize = 20;
int bgColor = 220;
String data_url = "http://where_people_look.s3.amazonaws.com/";
String data_url = "images/";
int debug_mode = 0;

// Globals and state variables
PImage[] images;
float[] kernel;
color sharp_p;
color blurry_p;
float mouse_x, mouse_y;
float start_time = 0;

int update = 1;
int setup_mode = 1;

void setup() {
  frameRate(20);
  kernel = make_kernel(doubling_radius, num_levels);

  // Load the image blur stack to explore.
  // Toggle setup_mode to display gray screen with blue dot.
  // In order, images are blurriest, blurry, and sharp.
  setup_mode = 1;
  images = new PImage[3];
  images[0] = requestImage(data_url+img+"_blur8.jpeg");
  images[1] = requestImage(data_url+img+"_blur4.jpeg");
  images[2] = requestImage(data_url+img+"_blur2.jpeg");
  images[3] = requestImage(data_url+img);
  if (debug_mode) println(data_url+img);
}

void update_pos() {
  mouse_x = mouseX;
  mouse_y = mouseY;
  if (javascript != null) {
    javascript.recordData(mouseX,mouseY,millis()-start_time,frameCount);
  }
}

void mouseMoved() {
  update = 1;

  // In 'free' mode, focus follows the mouse location
  if (!setup_mode && mode == "free") {
    update_pos();
  }
}

void mouseClicked() {
  update = 1;

  // In setup mode, check whether the click was inside the setup circle
  // and that the worker has accepted the HIT.
  if (setup_mode &&
      mouseX>images[0].width/2-csize &&
      mouseX<images[0].width/2+csize &&
      mouseY>images[0].height/2-csize &&
      mouseY<images[0].height/2+csize) {
    if (javascript != null && !javascript.HIT_accepted()) {
      javascript.alert("You must first accept the HIT!");
    } else {
      setup_mode = 0;
      start_time = millis();
    }
  }

  // In 'click' mode, focus only switches on clicks.
  if (!setup_mode && mode == "click") {
    update_pos();
  }
}

int all_images_loaded = 0;
void draw() {
  // Skip frames until done loading all images
  if (!all_images_loaded) {
    int still_loading = 0;
    for (int i=0; i<images.length; i++) {
      if (images[i].width == 0 && images[i].height == 0) {
        still_loading = 1;
      } else if (images[i].width == -1 || images[i].height == -1) {
        println("Error loading image!");
      }
    }
    if (!still_loading) {
      for (int i=0; i<images.length; i++) {
        images[i].resize(int(images[i].width*0.8), 0);
      }
      all_images_loaded = 1;
      if (debug_mode) println("Ready to go at "+millis()+" ms");
    }
  } else {
    // Resize the processing canvas to be exactly the size of the image
    if (width != images[0].width || height != images[0].height) {
      size(images[0].width,images[0].height);
    }

    if (debug_mode && frameCount % 25 == 0) {
      println(frameRate);
    }

    // If in setup mode, just display a circle in the middle of the image area.
    if (setup_mode) {
      background(bgColor);
      ellipse(images[0].width/2,images[0].height/2,csize,csize);
      fill(color(100,100,200));

    // Otherwise, if update mode is on (mouse has moved), display the image
    // and stuff.
    } else if (update) {
      image(images[0],0,0);
      loadPixels();
      for (int y=0; y<diameter; y++) {
        for (int x=0; x<diameter; x++) {
          int pos = y*diameter+x;
          if (kernel[pos] <= 0.125) {
            continue;
          } else if (kernel[pos] <= 0.25) {
            float upper_layer_proportion = (kernel[pos]-0.125)/(0.25-0.125);
            PImage upper_img = images[1];
            PImage lower_img = images[0];
          } else if (kernel[pos] <= 0.5) {
            float upper_layer_proportion = (kernel[pos]-0.25)/(0.5-0.25);
            PImage upper_img = images[2];
            PImage lower_img = images[1];
          } else {
            float upper_layer_proportion = (kernel[pos]-0.5)/(1-0.5);
            PImage upper_img = images[3];
            PImage lower_img = images[2];
          }
          layer_alpha = int(255*upper_layer_proportion);

          int img_pos = constrain(mouse_y-max_radius+y,0,images[0].height)*images[0].width + constrain(mouse_x-max_radius+x,0,images[0].width);

          layer_p = (upper_img.pixels[img_pos] & 0xffffff) | (layer_alpha << 24);
          bg_p = (lower_img.pixels[img_pos] & 0xffffff) | ((255-layer_alpha) << 24);
          pixels[img_pos] = blendColor(layer_p,bg_p,BLEND);
        }
      }
      updatePixels();
      update = 0;
    }
  }
}

float[] make_kernel(int doubling_radius, int num_levels) {
  // Return an array that has values of the foveal fall-off
  // function for all pixels in a square determined by the number
  // of levels and the doubling radius.
  float[] kernel = new float[4*max_radius*max_radius];
  for (int x=0; x<diameter; x++) {
    float x_s = (x-max_radius)*(x-max_radius);
    for (int y=0; y<diameter; y++) {
      float y_s = (y-max_radius)*(y-max_radius);
      float dist = sqrt(x_s + y_s);
      kernel[y*diameter+x] = pow(2, -dist/doubling_radius);
    }
  }
  return kernel;
}
