$(document).ready(function(){
	var imgSrcArray = [];
	var so = localStorage.getItem('storyObject') || JSON.stringify({});
	var currentTileId;
	so = JSON.parse(so);
	imgSrcArray = so.tiles || [];
	var currentTileId = parseInt(so.currentTileId,10);
	forge.logging.info("Story Tile Page has loaded it seems!");
	forge.logging.info(so);
	
	// add new tile
	$('.toolbar-content').on('click', '.add-image', function(){
		//autoSave();
		// Select an image and return with a maximum width and height of 300px
		forge.file.getImage({width: 300, height: 300}, function (file) {
			getImage(file);	
		});
	});

	// set story name from local storage
	$('#story-title').html(so.storyName);

	// create thumbnail images for footer from storyobject
	$.each(imgSrcArray, createFooterThumbnails);

	function createFooterThumbnails(i,value){
		var img = document.createElement('img');
		img.src = value.imgSrc;
		img.setAttribute('tile-id', value.tileId);
		if(value.tileId == currentTileId){
			img.className += ' current-tile';
			loadContent(currentTileId);
			changeCurrentTileClass(img);
		}
		$('.main-section-footer').append(img);
		// add click handler to footer thumbnails
		$(img).click(function(e){
			// save the changes that were made to questions, answers, notes
			autoSave();
			// change the current tile in local storage
			currentTileId = e.target.getAttribute('tile-id');
			so.currentTileId = currentTileId;
			console.log(so);
			localStorage.setItem('storyObject', JSON.stringify(so));
			// change the class name
			changeCurrentTileClass(e.target);
			// populate text boxes
			loadContent(currentTileId);
		});
	}

	function loadContent(tileId){
		console.log(tileId);
		$('#question').val(so.tiles[tileId].question);
		$('#answer').val(so.tiles[tileId].answer);
		$('#prompt').val(so.tiles[tileId].prompt);
		$('#canvas-area').html(so.tiles[tileId].notes);
	}
	
	function autoSave(){
		if(isNaN(currentTileId)) return;
		so.tiles[currentTileId].question = $('#question').val();
		so.tiles[currentTileId].answer = $('#answer').val();
		so.tiles[currentTileId].prompt = $('#prompt').val();
		so.tiles[currentTileId].notes = $('#canvas-area').html();
		localStorage.setItem('storyObject', JSON.stringify(so));
	}

	function changeCurrentTileClass(el, prevTileId){
		// remove the class from previous current tile
		$.each($(".main-section-footer img"), function(i, val){
			$(val).removeClass('current-tile');
		});
		$(el).addClass('current-tile');
		// set canvas thumbnail
		$('.canvas img').attr('src',$(el).attr('src'));	
	}
	
	/* toolbar click handlers */
	

	// save
	$('.toolbar-content').on('click', '#save', function(){
		// empty the tiles in the deletedTiles list
 		$('.loading-icon').show();
		console.log("organized ", so.tiles);
		// update the current tile's question, answer, prompt and notes
		console.log(currentTileId);
		autoSave();
		so.storyName = $('#story-title').html();
		localStorage.setItem('storyObject', JSON.stringify(so));
		console.log(so.tiles);
		setTimeout(function(){ $('.loading-icon').hide();}, 500);
	});

	function organizeTiles(tiles){
		var count = 0;
		var flag = false;
		console.log(tiles); 
		$.each(tiles, function(i,tile){
			if(!flag && currentTileId == tile.tileId){
				currentTileId = count;
				flag = true;
			}
			$('[tile-id='+tile.tileId+']').attr('tile-id', count);
			tile.tileId = count++;
		});

	}
	// copy tile -- change the copy icon !
	$('.toolbar-content').on('click', '#copy', function(){
		// copy data from current tile (have to copy individually else they are the same object)
		// insert into local storage
		// create a new thumbnail image
		var newTile = {imgSrc:so.tiles[currentTileId].imgSrc, question:so.tiles[currentTileId].question, answer:so.tiles[currentTileId].answer, prompt:so.tiles[currentTileId].prompt, comments:so.tiles[currentTileId].comments, notes:so.tiles[currentTileId].notes, tileId:so.tiles.length};
		so.tiles.push(newTile);
		so.currentTileId = newTile.tileId;
		currentTileId = newTile.tileId;
		localStorage.setItem('storyObject', JSON.stringify(so));
		console.log(so.tiles);
		createFooterThumbnails(0,so.tiles[currentTileId]);		
	});

	// delete tile
	$('.toolbar-content').on('click', '#delete', function(){
		// hide selected tile
		var deletedTileId = currentTileId;
		//$('.main-section-footer img.current-tile').hide();
		$('[tile-id='+currentTileId+']').hide().attr('tile-id',-99);
		//$('[tile-id='+currentTileId+']').setAttribute('tile-id',-99);
		currentTileId = (currentTileId > 0) ? currentTileId-1 : 1;
		// check if last tile
	
		changeCurrentTileClass($('[tile-id='+currentTileId+']'));
		loadContent(currentTileId);
		so.deletedTiles.push(deletedTileId);	
		so.tiles.splice(deletedTileId,1);
		organizeTiles(so.tiles);
		console.log(so.tiles);
	});

	// clear local storage
	$('.toolbar-content').on('click', '#off', function(){
		//$('#canvas-area').append("<div style='width:50px; height:20px; border:1px solid #333; background-image:url(img/comments.png) no-repeat'></div>");
		localStorage.clear();
		readyPage();
	});
});
function getImage(file){
	// set story name from local storage
	var so = localStorage.getItem('storyObject') || JSON.stringify({});
	so = JSON.parse(so);
	$('#story-title').html(so.storyName || 'Story Name');
	//var imgSrc = event.target.getAttribute('src');
	var imgSrc;
	var tileObject = {imgSrc:'', question:'', answer:'', prompt:'', comments:'', notes:'Notes: ', tileId:''};
	// Get a URL to the returned file object which can be used from the local webview.
	forge.logging.log("going to get url now");
	forge.file.URL(file, function (url) {
		forge.logging.info(url);
		imgSrc = url;
		console.log(so);
		if(!$.isEmptyObject(so)){
			tileObject.imgSrc = imgSrc;
			tileObject.tileId = so.tiles.length;
			so.currentTileId = so.tiles.length;
			so.tiles.push(tileObject);
			localStorage.setItem('storyObject', JSON.stringify(so));
		}else{
			so = {tiles:[], currentTileId:0, storyName:'Story Name', deletedTiles:[]};
			tileObject.imgSrc = imgSrc;
			tileObject.tileId = 0;
			so.tiles.push(tileObject);
			console.log(so);
			localStorage.setItem('storyObject', JSON.stringify(so));
		}
		forge.logging.info(localStorage.getItem('storyObject'));
		window.location = 'story_tile.html';
	});
}



