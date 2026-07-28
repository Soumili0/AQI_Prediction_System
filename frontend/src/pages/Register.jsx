import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import toast from 'react-hot-toast';
import { MdVisibility, MdVisibilityOff } from 'react-icons/md';
import useAuthStore from '../store/authStore';

const schema = yup.object({
  first_name: yup.string().required('First name is required'),
  last_name:  yup.string().required('Last name is required'),
  username:   yup.string().min(3, 'Min 3 chars').max(50).required('Username is required'),
  email:      yup.string().email('Invalid email').required('Email is required'),
  password:   yup.string()
    .min(8, 'Min 8 characters')
    .matches(/[A-Z]/, 'Must contain uppercase')
    .matches(/[a-z]/, 'Must contain lowercase')
    .matches(/\d/, 'Must contain a number')
    .matches(/[@$!%*?&_\-#]/, 'Must contain a special character')
    .required('Password is required'),
  confirm_password: yup.string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('Please confirm your password'),
  role:         yup.string().oneOf(['citizen', 'researcher', 'policy_maker']),
  organization: yup.string(),
  city:         yup.string(),
  country:      yup.string(),
});

export default function Register() {
  const navigate = useNavigate();
  const { register: registerUser, isLoading } = useAuthStore();
  const [showPw, setShowPw] = useState(false);
  const [success, setSuccess] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: yupResolver(schema),
    defaultValues: { role: 'citizen' },
  });

  const onSubmit = async (data) => {
    const { confirm_password, ...payload } = data;
    const result = await registerUser(payload);
    if (result.success) {
      setSuccess(true);
      toast.success(result.message || 'Registration successful!');
    } else {
      toast.error(result.error);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center animate-slide-up">
          <div className="text-5xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Registration Successful!</h2>
          <p className="text-gray-500 mb-6">Please check your email to verify your account before logging in.</p>
          <Link to="/login" className="btn-primary">Go to Login</Link>
        </div>
      </div>
    );
  }

  const Field = ({ name, label, type = 'text', placeholder, extra }) => (
    <div>
      <label className="label">{label}</label>
      <input type={type} placeholder={placeholder} className="input" {...register(name)} {...extra} />
      {errors[name] && <p className="text-red-500 text-xs mt-1">{errors[name].message}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="text-4xl mb-2">🌍</div>
          <h1 className="text-3xl font-bold text-white">Create Account</h1>
          <p className="text-blue-200 mt-1">Join the AQI Prediction community</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8 animate-slide-up">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field name="first_name" label="First Name" placeholder="John" />
              <Field name="last_name"  label="Last Name"  placeholder="Doe" />
              <Field name="username"   label="Username"   placeholder="john_doe" />
              <Field name="email"      label="Email"      type="email" placeholder="john@example.com" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <input type={showPw ? 'text' : 'password'} placeholder="Strong password"
                    className="input pr-10" {...register('password')} />
                  <button type="button" onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                    {showPw ? <MdVisibilityOff size={18}/> : <MdVisibility size={18}/>}
                  </button>
                </div>
                {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
              </div>
              <Field name="confirm_password" label="Confirm Password" type="password" placeholder="Repeat password" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="label">Role</label>
                <select className="input" {...register('role')}>
                  <option value="citizen">Citizen</option>
                  <option value="researcher">Researcher</option>
                  <option value="policy_maker">Policy Maker</option>
                </select>
              </div>
              <Field name="city"    label="City"    placeholder="Delhi" />
              <Field name="country" label="Country" placeholder="India" />
            </div>

            <Field name="organization" label="Organization (optional)" placeholder="Your institution" />

            <button type="submit" disabled={isLoading} className="btn-primary w-full py-3 text-base mt-2">
              {isLoading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-primary font-medium hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
