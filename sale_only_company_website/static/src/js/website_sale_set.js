odoo.define('sale_only_company.address', function (require) {
"use strict";

require('web.dom_ready');
var ajax = require('web.ajax');
var Widget = require('web.Widget');
var base = require('web_editor.base');
var website_sale_utils = require('website_sale.utils');
var weContext = require("web_editor.context");

if(!$('.oe_website_sale').length) {
    return $.Deferred().reject("DOM doesn't contain '.oe_website_sale'");
}

var SaleOnlyCompany = Widget.extend({
    init: function(){
        var self = this;
        //Search section
        $('.oe_website_sale .company_only_search_class').on('submit', function (event) {
            var $this = $(this);
            if (!event.isDefaultPrevented() && !$this.is(".disabled")) {
                event.preventDefault();
                var oldurl = $this.attr('action');
                oldurl += (oldurl.indexOf("?")===-1) ? "?" : "";
                var search = $this.find('input.search-query');
                window.location = oldurl + '&' + search.attr('name') + '=' + encodeURIComponent(search.val());
            }
        });
    }
});

new SaleOnlyCompany();

});
