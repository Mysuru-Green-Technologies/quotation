$(document).ready(function () {
    // Initialize profile functionality
    initProfilePage();
});

function initProfilePage() {
    // Set default avatar if custom one doesn't exist
    setDefaultAvatar();
    
    // Initialize modal functionality
    initPasswordModal();
    
    // Initialize avatar upload functionality
    initAvatarUpload();
}

function setDefaultAvatar() {
    const avatarImg = $('.avatar-img');
    avatarImg.on('error', function() {
        // Fallback to default avatar if specified image doesn't exist
        $(this).attr('src', "{{ url_for('static', filename='images/default-avatar.png') }}");
    });
}

function initPasswordModal() {
    // Show change password modal
    $('#changePasswordBtn').on('click', function () {
        try {
            $('#changePasswordModal').modal('show');
        } catch (error) {
            console.error('Modal error:', error);
            alert('Unable to open password change dialog');
        }
    });

    // Validate password form
    $('#passwordForm').on('submit', function (e) {
        const newPassword = $('#newPassword').val().trim();
        const confirmPassword = $('#confirmPassword').val().trim();

        if (newPassword.length < 8) {
            showAlert('Password must be at least 8 characters long');
            e.preventDefault();
            return false;
        }

        if (newPassword !== confirmPassword) {
            showAlert('Passwords do not match');
            e.preventDefault();
            return false;
        }

        return true;
    });
}

function initAvatarUpload() {
    // Avatar upload button triggers file input
    $('.avatar-upload-btn').on('click', function (e) {
        e.preventDefault();
        $('#avatarUpload').trigger('click');
    });

    // Handle avatar image selection
    $('#avatarUpload').on('change', function () {
        const file = this.files[0];
        const maxSizeMB = 2;
        
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            showAlert('Please select a valid image file (JPEG, PNG)');
            return;
        }

        // Validate file size (2MB max)
        if (file.size > maxSizeMB * 1024 * 1024) {
            showAlert(`Image must be smaller than ${maxSizeMB}MB`);
            return;
        }

        // Preview image
        previewImage(file);
        
        // Submit form
        $('#avatarForm').submit();
    });
}

function previewImage(file) {
    const reader = new FileReader();
    
    reader.onloadstart = function() {
        $('.avatar-img').addClass('loading');
    };
    
    reader.onload = function(e) {
        $('.avatar-img')
            .attr('src', e.target.result)
            .removeClass('loading');
    };
    
    reader.onerror = function() {
        showAlert('Error reading image file');
        $('.avatar-img').removeClass('loading');
    };
    
    reader.readAsDataURL(file);
}

function showAlert(message) {
    // You can replace this with a prettier notification system
    alert(message);
}