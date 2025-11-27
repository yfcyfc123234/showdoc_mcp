package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize
import kotlin.collections.MutableList

/**
 * 获取首页banner及功能区配置 (HomelistBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4461
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "home_banner": [
 *       {
 *         "title": "",
 *         "img": "http://newface.cdn.lifenhui.com/20240919/202409191736126958690.png",
 *         "data": "",
 *         "redirect": "",
 *         "category": "app",
 *         "type": "1",
 *         "version": "100",
 *         "vip": "0",
 *         "args": ""
 *       },
 *       {
 *         "title": "",
 *         "img": "http://newface.cdn.lifenhui.com/20240919/202409191736282511030.png",
 *         "data": "",
 *         "redirect": "",
 *         "category": "app",
 *         "type": "1",
 *         "version": "100",
 *         "vip": "0",
 *         "args": ""
 *       }
 *     ],
 *     "travel_banner": [
 *       {
 *         "title": "",
 *         "img": "http://newface.cdn.lifenhui.com/20240919/202409191736403824938.png",
 *         "data": "",
 *         "redirect": "",
 *         "category": "app",
 *         "type": "1",
 *         "version": "100",
 *         "vip": "0",
 *         "args": ""
 *       },
 *       {
 *         "title": "",
 *         "img": "http://newface.cdn.lifenhui.com/20240919/202409191736519131378.png",
 *         "data": "",
 *         "redirect": "",
 *         "category": "app",
 *         "type": "1",
 *         "version": "100",
 *         "vip": "0",
 *         "args": ""
 *       }
 *     ]
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class HomelistBean(
    var home_banner: MutableList<HomeBannerBean>,
    var travel_banner: MutableList<TravelBannerBean>
) : Parcelable


/**
 * HomeBannerBean
 */
@Parcelize
data class HomeBannerBean(
    var title: String,
    var img: String,
    var data: String,
    var redirect: String,
    var category: String,
    var type: String,
    var version: String,
    var vip: String,
    var args: String
) : Parcelable

/**
 * TravelBannerBean
 */
@Parcelize
data class TravelBannerBean(
    var title: String,
    var img: String,
    var data: String,
    var redirect: String,
    var category: String,
    var type: String,
    var version: String,
    var vip: String,
    var args: String
) : Parcelable