//story_play_initial_state
$(document).ready(function(){
	var so = localStorage.getItem('storyObject') || JSON.stringify({});
	var currentTileId;
	so = JSON.parse(so);
	console.log(so);
	var currentTileId = so.currentTileId;
	// display first question 
	function setupQuestion(){
		$('#question-text').html(so.tiles[currentTileId].question);
		$('#question-img img').attr('src', so.tiles[currentTileId].imgSrc);
		if(!$.isEmptyObject(so.selectedStudent)){
			$('#users').attr('src', so.selectedStudent.imgSrc);
		}
	}
	setupQuestion();

	$('#next-question').on('click', function(){
		if(currentTileId < so.tiles.length-1){
			currentTileId++;
			setupQuestion();
		}
	})

	$('.answer-tag').on('click', function(){
			$('.btn-container').show();
			$(this).hide();
			$('.main-section-footer').addClass('show-options');
	})
});