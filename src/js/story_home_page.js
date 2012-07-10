function forEach(arr, action){
  var len = arr.length,
  i=0;
  for(;i<len;i++){
    action(arr[i]);
  }
}
function filter(arr, condition){
  var results = [];
  forEach(arr, function(i){
    if(condition(i))
      results.push(i);
  });
  return results;
}

$(document).ready(function(){
  var so = localStorage.getItem('storyObject') || JSON.stringify({});
  so = JSON.parse(so);
  var selectedStudents = so.selectedStudents || [];
  console.log(so); 

  function setupStoryDetails(){
    // thumbnail
    if(!$.isEmptyObject(so)){
      //$('.big-thumbnail').attr('src', so.tiles[0].imgSrc);
      // story title
      if(so.storyName != 'Story Name')
        $('#story-title').val(so.storyName);
      if(so.storyDescription)
        $('#story-desc').val(so.storyDesc);
      if(so.storyTags)
        $('#story-tags').val(so.storyTags);
    }
    // show selected students if they exist
    if(selectedStudents.length){
      $.each(selectedStudents, function(index, val){
        addToSelectedStudents(val, true);
      });
    }
  }
  setupStoryDetails();
  
  function addToSelectedStudents(student,cacheFlag){
    if(cacheFlag !== true){
      // add to the array - push to local storage when save is clicked
      selectedStudents.push(student);
    }
    // TODO check if already added to DOM?
    // if yes then don't add to the container
    // insert the image into the screen
    $('.selected-students-container').append("<div class='selected-student' style='background:url("+student.img+") no-repeat center center'> <span>"+student.name+"</span></div>");
  }
  
  var values = AVAZ.students;
  // values to be passed to the autocomplete method is an array of objects with the property of value
  // when a particular value is selected, a callback function is called with the entire object
  $('#students').autocomplete({values:values, key:'name'},
    function(student){
      console.log(student);
      // insert the image into the screen
      addToSelectedStudents(student);
      $('#students').val('');
  });
  function save(){
    so.storyName =  $('#story-title').val();
    so.storyTags =  $('#story-tags').val();
    so.storyDesc =  $('#story-desc').val();
    so.selectedStudents = selectedStudents;
    localStorage.setItem('storyObject', JSON.stringify(so));    
  }

  $('.start-story').on('click', '.j-play-story', function(){
    $('.loading-icon').show();
    so.currentTileId = 0;
    so.selectedStudent = {};
    save();
    setTimeout(function(){ 
      $('.loading-icon').hide();
      window.location = 'story_play_initial_state.html';
    }, 
    500);
  });

  // story tiles button
  $('#story-tiles').on('click', function(){
    window.location = 'story_tile.html'
  });

  // clear local storage
  $('.toolbar-content').on('click', '#off', function(){
    //$('#canvas-area').append("<div style='width:50px; height:20px; border:1px solid #333; background-image:url(img/comments.png) no-repeat'></div>");
    localStorage.clear();
    window.location = 'story_home_page.html'
  });

});