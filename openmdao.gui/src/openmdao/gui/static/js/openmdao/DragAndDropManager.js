
var openmdao = (typeof openmdao === "undefined" || !openmdao ) ? {} : openmdao ;

openmdao.DragAndDropManager=function() {

    /***********************************************************************
     *  private
     ***********************************************************************/

    var self = this,
    droppables= new Hashtable();
    highlighting_droppables= new Hashtable();

    this.top_div_determined = false ;

    this.drop_target = null ;

    /** add droppable to droppables list. */
    this.addDroppable = function(droppable) {
        if (! droppables) {
            droppables = new Hashtable();
        }

        var elm = droppable ;
        while ( elm.css( "z-index" ) == "auto" )
        {
            elm = elm.parent();
        }

        droppables.put(droppable[0].id, elm.css( "z-index" ) );

    };

    /** remove droppable to droppables list. */
    this.removeDroppable = function(droppable) {
        if (! droppables) {
            return ;
        }

        droppables.remove(droppable.id);

    };

    /** clear all droppables */
    this.clearDroppables = function() {
        droppables.clear();
    };


    /** get top div that contains the draggable, is visible and accepts the 
     type of the draggable */
    this.getTopDroppableForDropEvent = function(ev, ui) {
        if (! droppables) {
            /* should not happen!! */
            return 0 ;
        }

        /* Which div that is visible and contains the cursor, 
           has the highest z-index */
        var max_zindex = -10000 ;
        var max_id = null ;
        droppables.each( function( id, zindex ) { 
            /* Check to see if this div is visible and contains the cursor */
            var div = $( id ) ;
            if ( openmdao.drag_and_drop_manager.isCursorInDiv( div, ui ) ) {
                if ( zindex > max_zindex ) 
                {
                    max_id = id ;
                    max_zindex = zindex ;
                }
            }
        } ) ;
        
        var div_on_top = $( max_id ) ;
        var div_on_top_object = jQuery( div_on_top ) ;
        
        return div_on_top_object ;
    };


    /** get top div that contains the draggable, is visible and accepts the 
     type of the draggable */
    this.getTopDroppableForDropEvent_ver2 = function(ev, ui) {
        if (! droppables) {
            /* should not happen!! */
            return 0 ;
        }




        return openmdao.drag_and_drop_manager.drop_target ;





        /* Which div that is visible and contains the cursor, 
           has the highest z-index */
        var max_zindex = -10000 ;
        var max_id = null ;
        var div = null ;
        var calculated_zindex = null ;
        droppables.each( function( id, zindex ) { 
            
            debug.info( "id and zindex", id, zindex ) ;
            
            /* Check to see if this div is visible and contains the cursor */
            div = $( id ) ;
            div_object = jQuery( div ) ;

            var elm = div_object ;
            while ( elm.css( "z-index" ) == "auto" )
            {
                elm = elm.parent();
            }

            calculated_zindex = elm.css( "z-index" ) ;

            debug.info( "calculated zindex" , elm.css( "z-index" ) ) ;

            if ( calculated_zindex > max_zindex ) 
            {
                max_id = id ;
                max_zindex = calculated_zindex ;
            }
        } ) ;
        
        var div_on_top = $( max_id ) ;
        //var div_on_top_object = jQuery( div_on_top ) ;
        var div_on_top_object = jQuery( "#" + max_id ) ;
        
        return div_on_top_object ;
    };


    this.isCursorInDiv = function(div,ui) {
        var left, right, top, bottom ;
        var drop_location_top = ui.offset.top ;
        var drop_location_left = ui.offset.left ;

        /* The width and height of the dropppable div does not correspond
           to the visual representation of the div. Need to use an ancestor of the div
        */ 
        /* this code only works for the "-dataflow" ID */
        if (div.parentNode.id.substring(0, 2) == "CE") {
            top = div.parentNode.parentNode.parentNode.parentNode.getBoundingClientRect().top ;
            bottom = div.parentNode.parentNode.parentNode.parentNode.getBoundingClientRect().bottom ;
            left = div.parentNode.parentNode.parentNode.parentNode.getBoundingClientRect().left ;
            right = div.parentNode.parentNode.parentNode.parentNode.getBoundingClientRect().right ;
        }
        else { /* this works for the other dataflows and slots */
            top = div.parentNode.parentNode.getBoundingClientRect().top ;
            bottom = div.parentNode.parentNode.getBoundingClientRect().bottom ;
            left = div.parentNode.parentNode.getBoundingClientRect().left ;
            right = div.parentNode.parentNode.getBoundingClientRect().right ;
        }

        if ( getComputedStyle( div.parentNode.parentNode ).display == "block" ) {
            if ( ( top < drop_location_top ) 
                 && 
                 ( drop_location_top < bottom )
                 &&
                 ( left < drop_location_left )
                 && 
                 (drop_location_left < right ) 
               )
            {
                return 1 ;
            }
            else {
                return 0 ;
            }
        }
        else {
            return 0 ;
        }
        
    };

    this.draggableOut = function(droppable) {
        
        var o = droppable.data('corresponding_openmdao_object');
        o.unhighlightAsDropTarget() ;
        highlighting_droppables.remove(droppable[0].id);
        
        openmdao.drag_and_drop_manager.updateHighlighting() ;
    };

    this.draggableOver = function(droppable) {
        if (! highlighting_droppables) {
            highlighting_droppables = new Hashtable();
        }

        var elm = droppable ;
        while ( elm.css( "z-index" ) == "auto" )
        {
            elm = elm.parent();
        }

        highlighting_droppables.put(droppable[0].id, elm.css( "z-index" ) );

        openmdao.drag_and_drop_manager.updateHighlighting() ;
    };

    /** clear all droppables */
    this.clearHighlightingDroppables = function() {
        highlighting_droppables.each( function( id, zindex ) { 
            var div = $( id ) ;
            var div_object = jQuery( div ) ;
            var o = div_object.data('corresponding_openmdao_object');
            o.unhighlightAsDropTarget()
        } ) ;
        highlighting_droppables.clear();
    };


    this.updateHighlighting = function() {

        // Find the div with the max id
        var max_zindex = -10000 ;
        var max_topmost_zindex = -10000 ;
        var max_id = null ;
        highlighting_droppables.each( function( id, zindex ) { 
            var div = $( id ) ;
            var div_object = jQuery( div ) ;
            var tmp_elm = div_object ;
            while ( tmp_elm.css( "z-index" ) == "auto" )
            {
                tmp_elm = tmp_elm.parent();
            }

            calculated_zindex = tmp_elm.css( "z-index" ) ;


            // Find the zindex for the topmost element
            tmp_elm = div_object  ;
            var topmost_zindex = null ;
            while ( 1 ) {
                if ( tmp_elm.css( "z-index" ) != "auto" ) {
                    topmost_zindex = tmp_elm.css( "z-index" ) ;
                }
                if ( ! tmp_elm.parent() ) {
                    break ;
                }
                if ( tmp_elm.parent().is( "body" ) ) {
                    break ;
                }
                tmp_elm = tmp_elm.parent() ;
            }
            topmost_zindex = tmp_elm.css( "z-index" ) ;

            if ( topmost_zindex > max_topmost_zindex ) {
                max_id = id ;
                max_zindex = calculated_zindex ;
                max_topmost_zindex = topmost_zindex ;
            } else if ( topmost_zindex == max_topmost_zindex ) {
                if ( calculated_zindex > max_zindex ) 
                {
                    max_id = id ;
                    max_zindex = calculated_zindex ;
                }
            }


        } ) ;
        
        // Now only highlight to top one
        highlighting_droppables.each( function( id, zindex ) { 
            var div = $( id ) ;
            var div_object = jQuery( div ) ;
            var o = div_object.data('corresponding_openmdao_object');
            if ( id == max_id ) {
                o.highlightAsDropTarget()

                openmdao.drag_and_drop_manager.drop_target = div_object ;


            } else {
                o.unhighlightAsDropTarget()
            }
        } ) ;

    };

}