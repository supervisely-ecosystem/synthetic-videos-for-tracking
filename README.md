<div align="center" markdown>


<img src="https://imgur.com/1wvvNyY.png"/>  

# Synthetic videos for tracking

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Watch-Demo-Video">Demo</a> •
    <a href="#Screenshots">Screenshots</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/synthetic-videos-for-tracking)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/synthetic-videos-for-tracking)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/synthetic-videos-for-tracking.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/synthetic-videos-for-tracking.png)](https://supervise.ly)

</div>

# Overview

App generates synthetic video data for tracking tasks. It copies labeled objects (foregrounds), applies augmentations and pastes them to background images according to the given parameters.

Application key points:
- Only `Bitmap` and `Polygon` shapes now available
- Video is created with a fixed background
- If the size of the object exceeds the size of the background, object size will be reduced
- If there are too many collisions between objects on the frame, we will warn you


<img src="https://github.com/supervisely-ecosystem/synthetic-videos-for-tracking/blob/master/demo/simple_video/demo1.gif?raw=true" style="max-width:50%;"/>


# How to Use

1. Label several objects as foregrounds using `Polygon` or `Bitmap` tools.  
For example you can use [Lemons (Annotated)](https://ecosystem.supervise.ly/projects/lemons-annotated) project from ecosystem.  
<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/lemons-annotated" src="https://imgur.com/SjUX1IZ.png" width="350px" style='padding-bottom: 10px'/>


2. Prepare backgrounds — it is a project or dataset with background images.  
For example you can use dataset `01_backgrounds` from project [Seeds](https://ecosystem.supervise.ly/projects/seeds).  
<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/seeds" src="https://imgur.com/dJPhe0r.png" width="350px" style='padding-bottom: 10px'/>


3. Add app from ecosystem to your team  
<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/synthetic-videos-for-tracking" src="https://imgur.com/WIjIxA1.png" width="350px" style='padding-bottom: 10px'/>



4. Run app from the context menu of project with labeled foregrounds:  
<img src="https://imgur.com/68J2Z6t.png" width="80%" style='padding-top: 10px'>  


5. Generate synthetic videos with different settings and save experiments results to different projects / datasets.

6. Close app manually


# Watch Demo Video
<a data-key="sly-embeded-video-link" href="https://youtu.be/yvWegId-edU" data-video-code="yvWegId-edU">
    <img src="https://imgur.com/VRQdPXx.png" alt="SLY_EMBEDED_VIDEO_LINK"  style="max-width:100%;">
</a>


# Screenshots
<img src="https://imgur.com/ezKOLE3.png" width="auto" style='padding-top: 10px'>
