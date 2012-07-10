var AVAZ = {};
AVAZ.students = [
				{name:'Akansha', img:'mock_images/students/akansha.jpg', _id:1}, 
				{name:'Gopal', img:'mock_images/students/gopal.jpg',  _id:2}, 
				{name:'Manohar', img:'mock_images/students/manohar.jpg', _id:3},
				{name:'Amit', img:'mock_images/students/amit.jpg', _id:4}, 
				{name:'Kumar', img:'mock_images/students/kumar.jpg', _id:5}, 
				{name:'Neha', img:'mock_images/students/neha.jpg', _id:6}, 
				{name:'Abhinav', img:'mock_images/students/abhinav.jpg', _id:7}, 
				{name:'Chirag', img:'mock_images/students/chirag.jpg', _id:8}, 
				{name:'Narayan', img:'mock_images/students/nadu.jpg', _id:9}, 
				{name:'Mayur', img:'mock_images/students/mayur.jpg', _id:10}, 
				{name:'Prateek', img:'mock_images/students/prateek.jpg', _id:11}, 
				{name:'Hasneen', img:'mock_images/students/hasneen.jpg', _id:12}, 
				{name:'Sneha', img:'mock_images/students/sneha.jpg', _id:13}, 
				{name:'Gurpreet', img:'mock_images/students/student.jpg', _id:14}, 
				{name:'Ramesh', img:'mock_images/students/ramesh.jpg', _id:15}, 
				{name:'Vikram', img:'mock_images/students/vikram.jpg', _id:16}
			]

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


(function($){
	$.fn.extend({
		//plugin name - autocomplete
		autocomplete:function(options, callback){
			var defaults = {
				values:[],
				callback: callback || function(){}
			};
			if(!options.key){
				console.log('Error - Key cannot be left blank');
				return;
			}
			var options = $.extend(defaults,options);
			return this.each(function(){
				$(this).bind('keyup', function(e){
					var typed = $(this).val();
					var autoValues;
					var values = options.values;
					var key = options.key;
					var regex = new RegExp(typed, "gi");
					var autocompleteEl = $('[autocomplete-for='+$(this).attr('id')+']');
					autocompleteEl.html('');
					autocompleteEl.hide();
					if(typed === '') {
						return; 
					}
					autoValues = filter(values, function(i){
						if(i[key].match(regex)){
							return true;
						}
						return false;
					});
					if(!autoValues.length) {
						autoValues[0] = {};
						autoValues[0][key] = 'No students found';
					}
					// append to autocomplete box
					var frag = document.createDocumentFragment();
					forEach(autoValues, function(i){
						var val = document.createElement('div');
						$(val).html(i[key]);
						$(val).addClass('autocomplete-element');
						$(val).data('valueObj',JSON.stringify(i));
						frag.appendChild(val);
					});
					autocompleteEl.append(frag);
					autocompleteEl.show();
				});

				$('[autocomplete-for]').on('click','.autocomplete-element',function(e){
					var inputEl = $(this).closest('[autocomplete-for]').attr('autocomplete-for');
					$('#'+inputEl).val($(this).html());
					$(this).closest('[autocomplete-for]').hide();
					if(typeof callback === 'function'){
						callback(JSON.parse($(this).data('valueObj')));
					}
				});

			});
		}
	})
}(jQuery));
