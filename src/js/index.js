$(document).ready(function(){
	$('.main-content').on("click", "#create-new-story", function(event){
		window.location = 'story_tile.html';
	});

	$('.main-content').on("click", "#edit-story", function(event){
		window.location = 'story_tile.html';
	});

	$('.main-content').on("click", "#play-story", function(event){
		window.location = 'story_home_page.html';
	});

	$('.container').on("click", ".j-play-story", function(event){
		window.location = 'story_home_page.html';
	});

})