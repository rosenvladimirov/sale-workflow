odoo.define('sale_product_set_website_sale.sets', function (require) {
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

var ProductSets = Widget.extend({
    events: {
        'click #my_sets': 'display_product_sets',
    },
    init: function(){
        var self = this;
        //console.log(self);
        this.product_set_ids = [];
        this.current_open_id = false;
        this.current_open_product_ids = false;
        var set_loading = $.get('/shop/sets', {'count': 1}).then(function(res) {
            self.product_set_ids = JSON.parse(res);
            console.log("JSON.parse(res) => self.product_set_ids=", self.product_set_ids);
            self.update_prodset_view();
        });

        $('.oe_website_sale .o_add_prodset, .oe_website_sale .o_add_prodset_dyn').click(function (e){
            self.add_new_products($(this), e);
        });
        //Search section
        $('.oe_website_sale .prodset_search_class').on('submit', function (event) {
        //$('.oe_search_box').on('click', function (event) {
            var $this = $(this);
            if (!event.isDefaultPrevented() && !$this.is(".disabled")) {
                event.preventDefault();
                var oldurl = $this.attr('action');
                oldurl += (oldurl.indexOf("?")===-1) ? "?" : "";
                var search = $this.find('input.search-query');
                window.location = oldurl + '&' + search.attr('name') + '=' + encodeURIComponent(search.val());
            }
        });
        if ($('.product-section').length) {
            // Manupolate products in sets
            $('.product-section a.o_product_set_rm').on('click', function (e){ self.product_rm(e, false); });
            $('.product-section a.o_product_set_add').on('click', function (e){
                $('.prodset-section a.o_product_set_add').addClass('disabled');
                self.product_add_or_mv(e).then(function(o) {
                    $('.product-section a.o_product_set_add').removeClass('disabled');
                });
            });
            // Manupolation of the sets
            $('.prodset-section a.o_prodset_rm').on('click', function (e){ 
                var current_open_id = self.current_open_id;
                console.log("Button dublicate", current_open_id, self);
                if (current_open_id !== false) {
                    ajax.jsonRpc('/shop/sets/remove/' + current_open_id)
                        .done(function (res) {
                            res = JSON.parse(res);
                            console.log("Remove res=", res);
                            if (res !== false) {
                                self.update_prodset_view();
                                console.log("Remove", res);
                                window.location = '/shop/sets';;
                            }
                    });
                }
                else {
                    alert("You can delete sets with status set to Draft only!");
                }
            });
            $('.prodset-section a.o_prodset_add').on('click', function (e){ self.product_set_add(e); });
            $('.prodset-section a.o_prodset_dublicate').on('click', function(e){
                var current_open_id = self.current_open_id;
                console.log("Button dublicate", current_open_id, self);
                if (current_open_id !== false) {
                    ajax.jsonRpc('/shop/sets/dublicate/' + current_open_id)
                        .done(function (res) {
                            res = JSON.parse(res);
                            console.log("Dublicate res=", res);
                            if (res !== false) {
                                self.update_prodset_view();
                                console.log("Dublicate", res);
                                location.reload(true);
                            }
                    });
                }
                else {
                    alert("You can duplicate sets with status set to Draft only!");
                }
            });
            $('.prodset-section a.o_prodset_edit')
                .off('click')
                .removeClass('a-submit')
                .click(_.debounce(function (e) {
                console.log("Edit modal", e);
                self.product_set_edit(e);
            }));
        }
        $('.oe_website_sale').on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function(ev) {
            var $ul = $(ev.target).closest('.js_add_cart_variants');
            var $parent = $ul.closest('.js_product');
            var $product_id = $parent.find('.product_id').first();
            var $el = $parent.find("[data-action='o_prodset']");
            if (!_.contains(self.current_open_product_ids, parseInt($product_id.val(), 10))) {
                $el.prop("disabled", false).removeClass('disabled').removeAttr('disabled');
            }
            else {
                $el.prop("disabled", true).addClass('disabled').attr('disabled', 'disabled');
            }
            $el.data('product-product-id', parseInt($product_id.val(), 10));
        });

        $('.oe_website_sale').on('change', "form.js_state_product_sets", function (event) {
            if (!event.isDefaultPrevented()) {
                event.preventDefault();
                var state = $(this).find("input[name='state']:checked").val();
                var current_id = $(this).attr('data');
                //console.log("State", state, "Current", current_id, "This", $(this));
                self.action_set_state(parseInt(current_id), state);
            }
        });

        // manage "List View of sets"
        $('.oe_website_sale').on('change', 'input.js_product_change', function(ev) {
            var product_id = ev.currentTarget.value;
            var $el = $(ev.target).closest('.js_add_cart_variants').find("[data-action='o_prodset']");

            if (!_.contains(self.current_open_product_ids, parseInt(product_id, 10))) {
                $el.prop("disabled", false).removeClass('disabled').removeAttr('disabled');
            }
            else {
                $el.prop("disabled", true).addClass('disabled').attr('disabled', 'disabled');
            }
            $el.data('product-product-id', product_id);
        });
        $('.oe_website_sale').on('click', 'a.js_add_pset_cart_json', function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.parent().find("input");
            var pset_id = +$input.closest('*:has(input[name="pset_id"])').find('input[name="pset_id"]').val();
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseInt($input.val(), 10) || 0;
            var new_qty = quantity > min ? (quantity < max ? quantity : max) : min;
            console.log("PSET", pset_id, $input);
            $('input[name="'+$input.attr("name")+'"]').add($input).filter(function () {
                var $pset = $(this).closest('*:has(input[name="pset_id"])');
                return !$pset.length || +$pset.find('input[name="pset_id"]').val() === pset_id;
            }).val(new_qty).change();
            return false;
        });

        set_loading.then(function() {
            if ($('input.js_product_change').length) { // manage "List View of sets"
                $('input.js_product_change:checked').first().trigger('change');
            }
            else {
                $('input.js_variant_change').trigger('change');
            }
        });

    },
    action_set_state: function(product_set_id, state){
        var self = this;
        ajax.jsonRpc('/shop/sets/state/' + product_set_id, 'call', {
            'state': state
            }).done(function (res) {
                self.update_prodset_view();
                console.log("Show", res);
            });
    },
    add_new_products: function($el, e){
        var self = this;
        var product_id = parseInt($el.data('product-product-id'), 10);
        if (!product_id && e.currentTarget.classList.contains('o_add_prodset_dyn')) {
            product_id = parseInt($el.parent().find('.product_id').val());
        }
        if (product_id) {
            return ajax.jsonRpc('/shop/sets/add', 'call', {
                'product_id': product_id,
                'product_set_id': self.current_open_id,
            }).then(function (current_set_id) {
                if (self.current_set_id !== current_set_id){
                    self.current_set_id = current_set_id;
                }
                if (current_set_id && !_.contains(self.product_set_ids, current_set_id)) {
                    self.product_set_ids.push(current_set_id);
                }
                self.update_prodset_view();
                website_sale_utils.animate_clone($('#my_sets'), $el.closest('form'), 25, 40);
                $el.prop("disabled", true).addClass('disabled');
                console.log("Pushing product_id=", product_id, " into current_set_id=", current_set_id);
            });
        }
    },
    display_product_sets: function() {
        if (this.product_set_ids.length === 0) {
            this.update_prodset_view();
            this.redirect_no_sets();
        }
        else {
            window.location = '/shop/sets';
        }
    },
    update_prodset_view: function() {
        var self = this;
        console.log("Updating product set id: ", this.product_set_ids);
        if (this.product_set_ids.length > 0) {
            $('#my_sets').show();
            $('.my_sets_quantity').text(this.product_set_ids.length);
            ajax.jsonRpc("/shop/sets/opened", 'call', {
                'opened': true,
                'kwargs': {
                   'context': _.extend({'display_product_set_product': true}, weContext.get())
                }}).then(function (res) {
                    console.log("Res=", res);
                    //var ret = JSON.parse(res);
                    if (res === false){
                        self.current_open_id = false;
                        self.current_open_product_ids = false;
                    } else {
                        self.current_open_id = res[0];
                        self.current_open_product_ids = res[1];
                    }
                    console.log("Current=", self, res);
                    if (self.current_open_id !== false) {
                        $('#show_sets').addClass('oe_product_set_open');
                    } else {
                        $('#show_sets').removeClass('oe_product_set_open');
                    }
                });
            console.log("Showing my sets - this.product_set_ids.lenght=", this.product_set_ids.length, this, self);

        } else {
            $('#my_sets').hide();
            console.log("Hiding my sets - this.product_set_ids.lenght=", this.product_set_ids.lenght);
        }
    },
    product_rm: function(e, deferred_redirect){
        var tr = $(e.currentTarget).parents('tr');
        var prodset = tr.data('prodset-id');
        var prodline = tr.data('prodline-id');
        var product = tr.data('product-id');
        var self = this;
        var current_set_id = self.current_open_id;
        console.log("Remove", e, deferred_redirect, prodset, prodline);
        ajax.jsonRpc('/shop/sets/product/remove/' + prodset + '/' + product).done(function (res) {
            $(tr).hide();
            current_set_id = res;
        });
        this.product_set_ids = _.without(this.product_set_ids, current_set_id);
        if (this.product_set_ids.length === 0) {
            deferred_redirect = deferred_redirect ? deferred_redirect : $.Deferred();
            deferred_redirect.then(function() {
                self.redirect_no_sets();
            });
        }
        this.update_prodset_view();
    },
    product_add_or_mv: function(e){
        return $('#b2b_prodset').is(':checked') ? this.product_add(e) : this.product_mv(e);
    },
    product_add: function(e){
        var tr = $(e.currentTarget).parents('tr');
        var product = tr.data('product-id');

        // can be hidden if empty
        $('#my_cart').removeClass('hidden');
        website_sale_utils.animate_clone($('#my_cart'), tr, 25, 40);
        return this.add_to_cart(product, tr.find('qty').val() || 1);
    },
    product_mv: function(e){
        var tr = $(e.currentTarget).parents('tr');
        var product = tr.data('product-id');

        $('#my_cart').removeClass('hidden');
        website_sale_utils.animate_clone($('#my_cart'), tr, 25, 40);
        var adding_deffered = this.add_to_cart(product, tr.find('qty').val() || 1);
        this.product_rm(e, adding_deffered);
        return adding_deffered;
    },
    product_set_edit: function(e){
        var self = this;
        var product_set = $(e.currentTarget).parent().attr('data');
        var $form = $(e.currentTarget).parent().parent().closest('form');

        e.preventDefault();
        console.log("Product_set=", product_set, $(e.currentTarget).parent(), $(e.currentTarget), $form, $(this));
        ajax.jsonRpc("/shop/sets/modal/" + product_set)
            .done(function (modal) {
            console.log("Return modal", modal);
            var $modal = $(modal);
            $form.addClass('css_options');
            $modal.appendTo($form)
                .modal()
                .on('hidden.bs.modal', function () {
                    $form.removeClass('css_options'); // possibly reactivate opacity (see above)
                    //$(e.currentTarget).remove();
                });

            $modal.on('click', '.a-submit', function (ev) {
                var $a = $(ev.currentTarget);
                var name = $form.find('input[name="name"]').val();
                var code = $form.find('input[name="code"]').val();
                ajax.jsonRpc('/shop/sets/update_desc/' + product_set, 'call', {
                    'name': name,
                    'code': code,
                    'lang': weContext.get().lang,
                    }).done( function (res) {
                        self.update_prodset_view();
                        //console.log("Show=", res, $a);
                        window.location = '/shop/sets';
                    });
                $modal.modal('hide');
                ev.preventDefault();
            });
        });
        return false;
    },
    product_set_add: function(e){
        var current = $(e.currentTarget).parent().parent();
        var btn = $(e.currentTarget);
        var product_set = $(e.currentTarget).attr('value');

        console.log("Add", current, product_set, current.find('input[name="add_qty"]'));
        // can be hidden if empty
        $('#my_cart').removeClass('hidden');
        website_sale_utils.animate_clone($('#my_cart'), btn, 25, 40);
        return this.add_sets_to_cart(product_set, current.find('input[name="add_qty"]').val() || 1);
    },
    add_to_cart: function(product_id, qty_id) {
        var add_to_cart = ajax.jsonRpc("/shop/cart/update_json", 'call', {
            'product_id': parseInt(product_id, 10),
            'add_qty': parseInt(qty_id, 10),
            'display': false,
        });
        console.log("adding to cart");

//        add_to_cart.then(function(resp) {
//            if (resp.warning) {
//                if (! $('#data_warning').length) {
//                    $('.prodset-section').prepend('<div class="mt16 alert alert-danger alert-dismissable" role="alert" id="data_warning"></div>');
//                }
//                var cart_alert = $('.prodset-section').parent().find('#data_warning');
//                cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + resp.warning);
//            }
//            $('.my_cart_quantity').html(resp.cart_quantity || '<i class="fa fa-warning" /> ');
//        });
        return add_to_cart;
    },
    add_sets_to_cart: function(product_set_id, qty_id) {
        var add_sets_to_cart = ajax.jsonRpc("/shop/sets/cart/update_json", 'call', {
            'product_set_id': parseInt(product_set_id, 10),
            'set_qty': parseInt(qty_id, 10),
            'display': false,
        });

        add_sets_to_cart.then(function(resp) {
            if (resp.warning) {
                if (! $('#data_warning').length) {
                    $('.prodset-section').prepend('<div class="mt16 alert alert-danger alert-dismissable" role="alert" id="data_warning"></div>');
                }
                var cart_alert = $('.prodset-section').parent().find('#data_warning');
                cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + resp.warning);
            }
            $('.my_cart_quantity').html(resp.cart_quantity || '<i class="fa fa-warning" /> ');
        });
        return add_sets_to_cart;
    },

    redirect_no_sets: function() {
        window.location = '/shop/cart';
    }
});

new ProductSets();

});
