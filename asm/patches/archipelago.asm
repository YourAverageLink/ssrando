.open "main.dol"
;.org 0x80064b54 ; called every frame
;bl give_archipelago_item

.org 0x8005526c ; 4 free bytes in the dol that we can use to store a pointer to the text buffer
.long archipelago_text_buffer

.org 0x800b9270
b add_more_colors

; .org 0x802569c8 ; end of AcItem::addToGetQueue
; b increment_item_queue

.org 0x80256a4c ; end of AcItem::removeFromGetQueue
b decrement_item_queue

.close

.open "d_a_b_lastbossNP.rel"
.org 0x9B18 ; hard-code the actor to set story flag 959 when killed
bl set_demise_defeated_storyflag

.close