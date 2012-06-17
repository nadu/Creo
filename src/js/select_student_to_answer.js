$(document).ready(function(){
        var imgSrcArray = []; 
        var so = localStorage.getItem('storyObject') || JSON.stringify({});
        so = JSON.parse(so);
        var selectedStudents = so.selectedStudents.length ? so.selectedStudents : AVAZ.students ;
        // get the student images
        $.each(selectedStudents, function(index, student){
                console.log(student)
                $('.main-section').append("<div class='selected-student' data-student-img='"+student.img+"' data-student-id='"+student._id+"' style='background:url("+student.img+") no-repeat center center'> <span>"+student.name+"</span></div>");
        }); 

        $('.main-section').on('click', '.selected-student', function(){
                console.log($(this).attr('data-student-id'));
                so.selectedStudent = {imgSrc: $(this).attr('data-student-img'), _id:$(this).attr('data-student-id')};
                console.log(so);
                localStorage.setItem('storyObject', JSON.stringify(so));  
                window.location = 'story_play_initial_state.html';
        })  
});
