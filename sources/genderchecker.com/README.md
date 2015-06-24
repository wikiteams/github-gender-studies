GitHub-user gender recognition (v1.4)
=====================

#### Introduction

**Estimates gender of GitHub users (using their first name, and optionally - their dialogue acts) and puts this information for further analysis into a GitHub Torrent MySQL database**

##### License

The MIT License (MIT)

Copyright (c) 2015 WikiTeams.pl

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

##### Acknowledgements

We have an instance of GHTorrent as described on 'Georgios Gousios: The GHTorrent dataset and tool suite. MSR 2013: 233-236'

We use portal [genderchecker.com](http://genderchecker.com/) to estimate GitHub user gender, depending on his name.

Moreover, we use a 3rd party service available at [codejungle.org](http://www.codejungle.org/site/api.html#gender) to verify with smaller dataset but having more balanced gender-classified names.

If there is enough time, OpenCV with [FisherFaces algorithm](https://github.com/bytefish/facerec) will be used.

##### Requirements

For required libraries please check *requirements.txt*. Program does not guarantee compability with your local copy of GitHub Torrent MySQL databse, but feel free to contact me in case of any questions or problems.


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/wikiteams/github-gender-studies/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

