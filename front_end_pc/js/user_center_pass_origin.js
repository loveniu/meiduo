/**
 * Created by python on 18-7-10.
 */
var vm = new Vue({
    el: '#app',
    data: {
        host,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        username: '',
        old_password: '',
        password: '',
        password2: '',

        error_old_password: false,
        error_password: false,
        error_check_password: false,
        error_old_password_info: '密码最少8位，最长20位'
    },
    mounted: function () {
        // 判断用户的登录状态
        if (this.user_id && this.token) {
            axios.get(this.host + '/user/', {
                // 向后端传递JWT token的方法
                headers: {
                    'Authorization': 'JWT ' + this.token
                },
                responseType: 'json',
            })
                .then(response => {
                    // 加载用户数据
                    this.user_id = response.data.id;
                    this.username = response.data.username;
                })
                .catch(error => {
                    if (error.response.status == 401 || error.response.status == 403) {
                        location.href = '/login.html?next=/user_center_info.html';
                    }
                });
        } else {
            location.href = '/login.html?next=/user_center_info.html';
        }
    },
    methods: {
        // 退出
        logout: function () {
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },

        check_opwd: function () {
            var len = this.old_password.length;
            if (len < 1) {
                this.error_old_password = true;
                this.error_old_password_info = "请填写原密码"
            } else if (len < 8 || len > 20) {
                this.error_old_password = true;
            } else {
                this.error_old_password = false
            }
        },
        check_pwd: function () {
            var len = this.password.length;
            if (len < 8 || len > 20) {
                this.error_password = true;
            } else {
                this.error_password = false;
            }
        },
        check_cpwd: function () {
            if (this.password != this.password2) {
                this.error_check_password = true;
            } else {
                this.error_check_password = false;
            }
        },
        on_submit: function () {
            this.check_opwd();
            this.check_pwd();
            this.check_cpwd();
            if (this.error_old_password == false && this.error_password == false && this.error_check_password == false) {
                axios.put(this.host + '/users/' + this.user_id + '/password/', {
                    old_password: this.old_password,
                    password: this.password,
                    password2: this.password2,
                }, {
                    headers: {
                        'Authorization': 'JWT ' + this.token
                    },
                    responseType: 'json'
                })
                    .then(response => {
                        alert('密码修改成功');
                        location.href = '/login.html'
                    })
                    .catch(error => {
                        alert(error.response.data.message);
                        console.log(error.response.data);
                    })
            }
        }
    }
});