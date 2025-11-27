package com.cqfengli.api.entities.app.response

import android.os.Parcelable
import kotlinx.parcelize.Parcelize
import kotlin.collections.MutableList

/**
 * 开屏付费配置 (ConfBean)
 * 
 * 接口文档: https://doc.cqfengli.com/web/#/90/4462
 * 
 * 成功返回示例:
 * {
 *   "code": 1,
 *   "msg": "请求成功",
 *   "data": {
 *     "vip_list": [
 *       {
 *         "id": 102,
 *         "ali_name": "终身会员",
 *         "wx_name": "终身会员",
 *         "id_product": "0",
 *         "ali_price": 168,
 *         "wx_price": 168,
 *         "tag": "",
 *         "auto": 0,
 *         "checked": 1,
 *         "pay_config": [
 *           {
 *             "type": "2",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "app"
 *           },
 *           {
 *             "type": "1",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "app"
 *           }
 *         ]
 *       },
 *       {
 *         "id": 101,
 *         "ali_name": "连续包年",
 *         "wx_name": "年卡会员",
 *         "id_product": "0",
 *         "ali_price": 158,
 *         "wx_price": 198,
 *         "tag": "http://newface.cdn.lifenhui.com/20230818/202308181437431515311.png",
 *         "auto": 1,
 *         "checked": 2,
 *         "pay_config": [
 *           {
 *             "type": "2",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "web"
 *           },
 *           {
 *             "type": "1",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "app"
 *           }
 *         ]
 *       },
 *       {
 *         "id": 100,
 *         "ali_name": "连续包周",
 *         "wx_name": "周卡会员",
 *         "id_product": "0",
 *         "ali_price": 16,
 *         "wx_price": 20,
 *         "tag": "http://newface.cdn.lifenhui.com/20230818/202308181438011796191.png",
 *         "auto": 1,
 *         "checked": 2,
 *         "pay_config": [
 *           {
 *             "type": "2",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "web"
 *           },
 *           {
 *             "type": "1",
 *             "icon": "http://newface.cdn.lifenhui.com/20230818/202308181438123873710.png",
 *             "mode": "app"
 *           }
 *         ]
 *       }
 *     ],
 *     "face_list": [
 *       {
 *         "cover": "http://newface.cdn.lifenhui.com/cover/20230817/18_e58140bf172d6bf58cf7cd522dffc02f.png",
 *         "url": "http://newface.cdn.lifenhui.com/face_fusion/20230817/775936f60480d682c3ce8282ab37a2f9.mp4",
 *         "tpl_url": "http://newface.cdn.lifenhui.com/20230816/7bffd13fc2a4fe9038ea5e889305e3f5.mp4"
 *       },
 *       {
 *         "cover": "http://newface.cdn.lifenhui.com/cover/20230817/58_c51079fdcf41a744100e46f20402e252.png",
 *         "url": "http://newface.cdn.lifenhui.com/face_fusion/20230817/c11b352f42a5fcb967c3fe7b34ac6ae1.mp4",
 *         "tpl_url": "http://newface.cdn.lifenhui.com/20230816/c51079fdcf41a744100e46f20402e252.mp4"
 *       },
 *       {
 *         "cover": "http://newface.cdn.lifenhui.com/cover/20230817/108_b840c4db3d42139593a1b2df8f438eb8.png",
 *         "url": "http://newface.cdn.lifenhui.com/face_fusion/20230817/0aee5dedcedc69f2ecc496b32f1df6a3.mp4",
 *         "tpl_url": "http://newface.cdn.lifenhui.com/20230816/b840c4db3d42139593a1b2df8f438eb8.mp4"
 *       },
 *       {
 *         "cover": "http://newface.cdn.lifenhui.com/cover/20230817/111_a9782692cac6ee452633b3db6d70b54a.png",
 *         "url": "http://newface.cdn.lifenhui.com/face_fusion/20230817/6634cf5b2c230347b6d882608b5dcb8a.mp4",
 *         "tpl_url": "http://newface.cdn.lifenhui.com/20230816/a9782692cac6ee452633b3db6d70b54a.mp4"
 *       }
 *     ],
 *     "monthly": "http://newface.juyuwang.vip/monthly_az.html",
 *     "privacypolicy": "http://newface.juyuwang.vip/privacypolicy.html",
 *     "useragreement": "http://newface.juyuwang.vip/useragreement.html"
 *   },
 *   "hasNext": 0
 * }
 */
@Parcelize
data class ConfBean(
    var vip_list: MutableList<VipListBean>,
    var face_list: MutableList<FaceListBean>,
    var monthly: String,
    var privacypolicy: String,
    var useragreement: String
) : Parcelable


/**
 * PayConfigBean
 */
@Parcelize
data class PayConfigBean(
    var type: String,
    var icon: String,
    var mode: String
) : Parcelable

/**
 * VipListBean
 */
@Parcelize
data class VipListBean(
    var id: Int,
    var ali_name: String,
    var wx_name: String,
    var id_product: String,
    var ali_price: Int,
    var wx_price: Int,
    var tag: String,
    var auto: Int,
    var checked: Int,
    var pay_config: MutableList<PayConfigBean>
) : Parcelable

/**
 * FaceListBean
 */
@Parcelize
data class FaceListBean(
    var cover: String,
    var url: String,
    var tpl_url: String
) : Parcelable