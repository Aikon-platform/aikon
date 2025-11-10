/**
 * @typedef RegionItemType
 * @type {object}
 * @property {string} id
 * @property {string} img : either "wit<id>_<digit><id>_<page_nb>.jpg" or "wit<id>_<digit><id>_<page_nb>_<x,y,h,w>.jpg"
 * @property {string} title : title of the region (to be displayed in the overlay)
 * @property {number[]|string[]} xywh : [x, y, width, height]
 * @property {string} canvas : page number
 * @property {string} ref : unique reference to be copied in the clipboard
 * @property {string} type : always "Regions"
 */

export {}
