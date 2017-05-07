angular.module('app', ['ngSanitize'])

.constant('WORD_COUNT', 34307)

.config(["$sceDelegateProvider", function($sceDelegateProvider) {
    $sceDelegateProvider.resourceUrlWhitelist([
        "self",
        "http://upload.wikimedia.org/**"
    ]);
}])

.controller('WordController', function($scope, $locale, $http, $document, WORD_COUNT) {

  $scope.previousWord = undefined;
  $scope.nextWord = undefined;
  $scope.word = undefined;

  $scope.showNextWord = function() {
    $scope.rank++
    showWord($scope.rank);
  };

  $scope.showPreviousWord = function() {
    $scope.rank--;
    showWord($scope.rank);
  };

  $scope.hasNextWord = function() {
    return $scope.rank <= WORD_COUNT;
  };

  $scope.hasPreviousWord = function() {
    return $scope.rank >= 2;
  };

  function precheck(json) {
    json.copyByValue = true;

    // Precheck audio
    if (json.audio) {
      json.audio = {
        name: json.audio,
        url: json.audio_url,
        include: true
      }
    }

    // Precheck definitions
    filtered_types = [];
    for (var i = 0; i < json.types.length; i++) {
        var type = json.types[i];
        if (type.definitions.length > 0) {
            filtered_types.push(type);
        } else {
            continue; // ignore
        }
        type.include = true;
        for (var j = 0; j < type.definitions.length; j++) {
            definition = type.definitions[j];
            var outdated = definition.text.indexOf('archaic') !== -1 || definition.text.indexOf('dated') !== -1; // ignore old definitions
            definition.include = !outdated && i < 3 && j < 3; // Keep only 6 first definitions for 3 first types
            if (definition.quotations && definition.quotations.length > 0) {
                quotations = definition.quotations;
                definition.quotations = [];
                var shortestQuotationLength = Number.MAX_VALUE;
                var shortestQuotationIndex = -1;
                for (var k = 0; k < quotations.length; k++) {
                    // We want to include the shortest quotation only
                    if (quotations[k].length < shortestQuotationLength) {
                        shortestQuotationLength = quotations[k].length;
                        shortestQuotationIndex = k;
                    }
                    definition.quotations.push({
                        text: quotations[k],
                        include: false,    // set just after
                        card_sample: false // Create a flashcard "Fill the gap" at the demand
                    });
                }

                if (definition.include && shortestQuotationIndex != -1) {
                    definition.quotations[shortestQuotationIndex].include = true;
                }

            } else {
                delete definition['quotations']; // Quotations was systematically added in Python script
            }
        }
    }
    json.types = filtered_types;

    // Precheck synonyms
    if (json.synonyms) {
      synonyms = json.synonyms;
      json.synonyms = [];
      for (var i = 0; i < synonyms.length; i++) {
        json.synonyms.push({
            text: synonyms[i],
            include: i < 10 // Keep only 2 first synonyms
        });
      }
    }

    // Precheck translations
    if (json.translations) {
      translations = json.translations;
      json.card_translate = true; // Add a flashcard French -> English
      json.translations = [];
      for (var i = 0; i < translations.length; i++) {
        json.translations.push({
            text: translations[i],
            include: i < 6 // Keep only 3 first translations
        });
      }
    }

    // Precheck images
    json.card_image = false // Most word will not have a description image
    if (!json.images) {
        json.images = [];
    }
  }

  function pad(n, width, z) {
    z = z || '0';
    n = n + '';
    return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
  }

  function startTimer() {
    timer = document.getElementById('timer');
    timer.innerHTML = "--:--";
    timer.classList.remove("elapsed");

    this.i = 0;
    if (this.intervalID) {
      clearInterval(this.intervalID);
    }

    this.intervalID = window.setInterval(function() {
        i++;
        if (i == 15) {
            timer.classList.add("elapsed");
        }
        timer.innerHTML = pad(i, 2, "0") + ":00";
    }, 1000);

  }

  /*
   * Main method to display a word content.
   */
  function showWord(rank) {

    $http.get('/api/word/' + rank).then(function(json) {
      $scope.json = json.data;
      $scope.word = $scope.json.title;
      precheck($scope.json);
      startTimer();
    })

    if ($scope.hasPreviousWord()) {
      $http.get('/api/word/' + (rank - 1)).then(function(json) {
          $scope.previousWord = json.data.title;
      })
    }

     if ($scope.hasNextWord()) {
        $http.get('/api/word/' + (rank + 1)).then(function(json) {
            $scope.nextWord = json.data.title;
        })
     }

     window.location.hash = '#' + $scope.rank;
  }

  $scope.loadImages = function() {
    $http.get('/api/images/' + $scope.word).then(function(json) {
        images = json.data;
        for (var i = 0; i < images.length; i++) {
            var image = images[i];
            $scope.json.images.push({
                "description": image.title,
                "filename": image.link.substring(image.link.lastIndexOf('/') + 1),
                "thumb_url": image.image.thumbnailLink,
                "url": image.link
            });
        }
    });
  };

  /*
   * Save the currently edited JSON document before moving to the next word.
   */
  $scope.save = function() {
    $http.put('/api/word/' + $scope.rank, $scope.json).then(function() {
        $scope.showNextWord();
    });
  };


  if (window.location.hash) {
    $scope.rank = Number(window.location.hash.substring(1));
  } else {
    $scope.rank = 1;
  }
  showWord($scope.rank);

  // Assign hotkeys
  $document.bind("keypress", function(event) {
    code = event.charCode || event.keyCode;
    //console.log(code);
    switch (code) {
    case 78: // N
    case 110: // n
        $scope.showNextWord();
        break;
    case 80: // P
    case 112: // p
        $scope.showPreviousWord();
        break;
    case 73:
    case 105:
        $scope.loadImages();
        break;
    case 13: // Enter
        $scope.save();
        break;
    }
  });

})

/*
 * Listen on checkbox click to highlight container parent element.
 */
.directive('mySelectable', ['$document', function($document) {
  return {
    link: function(scope, element, attr) {

      element.on('focus', function(event) {
        // Prevent default dragging of selected content
        event.preventDefault();
        element.parent().addClass('focused');
      });

      element.on('blur', function(event) {
        // Prevent default dragging of selected content
        event.preventDefault();
        element.parent().removeClass('focused');
      });

    }
  };
}]);
