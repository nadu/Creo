$(document).ready(function(){
	$("#create-new-story").on("click", function(event){
		window.location = 'story_tile.html';
	});

	$('#edit-story').on("click", function(event){
		window.location = 'story_tile.html';
	});

	$("#play-story").on("click", function(event){
		window.location = 'story_home_page.html';
	});

	$('.j-play-story').on("click", function(event){
		window.location = 'story_home_page.html';
	});

})