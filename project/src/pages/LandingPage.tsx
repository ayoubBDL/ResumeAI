import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Zap, DollarSign, Upload, Linkedin, Clock, Target, CheckCircle, ArrowRight, Menu } from 'lucide-react';
import logo from '../assets/logo.png';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm fixed w-full z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex-shrink-0 flex items-center gap-2">
              <img
                className="h-[100px] w-[100px] object-contain"
                src={logo}
                alt="ResumeAI Logo"
              />
            </div>
            <div className="hidden sm:flex sm:space-x-8">
              <a href="#features" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">Features</a>
              <a href="#how-it-works" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">How it Works</a>
              <a href="#pricing" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">Pricing</a>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-gray-500 hover:text-gray-900 px-3 py-2 text-sm font-medium">Sign in</Link>
              <Link to="/signup" className="bg-indigo-600 text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-indigo-700">Get Started</Link>
            </div>
            <button className="sm:hidden">
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <div className="relative pt-16">
        <div className="absolute inset-0">
          <img 
            src="https://images.unsplash.com/photo-1497032628192-86f99bcd76bc"
            alt="Professional workspace"
            className="w-full h-full object-cover opacity-65"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-gray-50/95 via-white/90 to-gray-50/95 mix-blend-overlay" />
        </div>
        <div className="relative max-w-7xl mx-auto py-24 px-4 sm:py-32 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
              Land Your Dream Job with an{' '}
              <span className="text-indigo-600">AI-Powered</span>
              <br />
              <span className="text-gray-900">Resume</span>
            </h1>
            <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-600">
              Transform your resume into a perfectly tailored match for any job in seconds. Upload once, customize for every application.
            </p>
            <div className="mt-10">
              <Link
                to="/signup"
                className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:text-lg md:px-10 transition-all duration-200 hover:shadow-lg"
              >
                Get Started Free{' '}
                <ArrowRight className="ml-2 -mr-1 w-5 h-5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <section className="bg-white py-20" id="how-it-works">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-8 max-w-6xl mx-auto">
            <div className="text-center p-6">
              <div className="relative">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto">
                  <Upload className="w-8 h-8 text-indigo-600" />
                </div>
                <div className="absolute top-1/2 left-full hidden md:block w-full border-t-2 border-dashed border-indigo-200"></div>
              </div>
              <h3 className="text-xl font-semibold mt-6 mb-3">1. Upload Resume</h3>
              <p className="text-gray-600">Upload your existing resume in any format (PDF, Word, or Text). Our AI will analyze your experience and skills.</p>
            </div>

            <div className="text-center p-6">
              <div className="relative">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto">
                  <Linkedin className="w-8 h-8 text-indigo-600" />
                </div>
                <div className="absolute top-1/2 left-full hidden md:block w-full border-t-2 border-dashed border-indigo-200"></div>
              </div>
              <h3 className="text-xl font-semibold mt-6 mb-3">2. Add Job Details</h3>
              <p className="text-gray-600">Paste the job URL or description. We support LinkedIn, Indeed, and other major job boards.</p>
            </div>

            <div className="text-center p-6">
              <div className="relative">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto">
                  <Zap className="w-8 h-8 text-indigo-600" />
                </div>
                <div className="absolute top-1/2 left-full hidden md:block w-full border-t-2 border-dashed border-indigo-200"></div>
              </div>
              <h3 className="text-xl font-semibold mt-6 mb-3">3. Get Optimized</h3>
              <p className="text-gray-600">Our AI tailors your resume to match the job perfectly, optimizing keywords and skills.</p>
            </div>

            <div className="text-center p-6">
              <div className="relative">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto">
                  <Target className="w-8 h-8 text-indigo-600" />
                </div>
              </div>
              <h3 className="text-xl font-semibold mt-6 mb-3">4. Track & Apply</h3>
              <p className="text-gray-600">Download your optimized resume and cover letter. Track your application status all in one place.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <div id="features" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-indigo-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to land your dream job
            </p>
          </div>

          <div className="mt-20">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <FileText className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Smart Analysis</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Our AI analyzes both your resume and job descriptions to identify key requirements and skills that need highlighting.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <Target className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Job Application Tracking</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Keep track of all your job applications in one place. Monitor status, save job posts, and manage your progress.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <Clock className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Application Status</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Track your applications from pending to interviewing. Get organized with status updates and never miss an opportunity.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <FileText className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Cover Letter Generation</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Generate tailored cover letters for each job application. Our AI helps you craft compelling cover letters that complement your resume.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <Zap className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Instant Results</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Get your tailored resume and cover letter in seconds. Real-time optimization feedback helps you improve your application instantly.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6">
                <div className="flow-root bg-white rounded-lg px-6 pb-8">
                  <div className="-mt-6">
                    <div>
                      <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                        <DollarSign className="h-6 w-6 text-white" />
                      </span>
                    </div>
                    <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">Affordable Plans</h3>
                    <p className="mt-5 text-base text-gray-500">
                      Start with 2 free tries, then choose a plan that fits your needs. No hidden fees, cancel anytime.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <section className="py-20 bg-white" id="pricing">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">Simple, Transparent Pricing</h2>
          <div className="grid md:grid-cols-4 gap-8 max-w-7xl mx-auto">
            {/* Free Plan */}
            <div className="border rounded-2xl p-8 hover:shadow-lg transition-shadow">
              <h3 className="text-2xl font-bold mb-4">Free Trial</h3>
              <p className="text-gray-600 mb-6">Perfect for testing the waters</p>
              <div className="text-4xl font-bold mb-6">$0</div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>2 free resume customizations</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>Basic AI optimization</span>
                </li>
              </ul>
              <Link 
                to="/signup" 
                className="w-full py-2 px-4 border-2 border-indigo-600 text-indigo-600 rounded-full hover:bg-indigo-50 transition-colors inline-block text-center"
              >
                Start Free
              </Link>
            </div>

            {/* Pay as you go */}
            <div className="border rounded-2xl p-8 hover:shadow-lg transition-shadow">
              <h3 className="text-2xl font-bold mb-4">Pay as You Go</h3>
              <p className="text-gray-600 mb-6">For occasional job seekers</p>
              <div className="text-4xl font-bold mb-6">$1<span className="text-xl font-normal">/try</span></div>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>Minimum $5 purchase</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>Full AI optimization</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>No commitment</span>
                </li>
              </ul>
              <Link 
                to="/signup" 
                className="w-full py-2 px-4 border-2 border-indigo-600 text-indigo-600 rounded-full hover:bg-indigo-50 transition-colors inline-block text-center"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="border-2 border-indigo-600 rounded-2xl p-8 hover:shadow-lg transition-shadow relative">
              <div className="absolute top-4 right-4 bg-indigo-600 text-white text-sm px-3 py-1 rounded-full">
                Most Popular
              </div>
              <h3 className="text-2xl font-bold mb-4">Pro</h3>
              <p className="text-gray-600 mb-6">For active job seekers</p>
              <div className="text-4xl font-bold mb-2">$29</div>
              <p className="text-sm text-gray-600 mb-6">50 credits per month</p>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>50 resume customizations</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>Advanced AI optimization</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-600" />
                  <span>Priority support</span>
                </li>
              </ul>
              <Link 
                to="/signup" 
                className="w-full py-2 px-4 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors inline-block text-center"
              >
                Get Pro
              </Link>
            </div>

            {/* Annual Plan */}
            <div className="border-2 border-green-600 rounded-2xl p-8 hover:shadow-lg transition-shadow relative bg-green-50">
              <div className="absolute top-4 right-4 bg-green-600 text-white text-sm px-3 py-1 rounded-full">
                Best Value
              </div>
              <h3 className="text-2xl font-bold mb-4">Annual</h3>
              <p className="text-gray-600 mb-6">For serious job seekers</p>
              <div className="text-4xl font-bold mb-2">$299</div>
              <p className="text-sm text-gray-600 mb-6">Unlimited credits for 1 year</p>
              <ul className="space-y-4 mb-8">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Unlimited optimizations</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Premium AI features</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>24/7 Priority support</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Save $49/month</span>
                </li>
              </ul>
              <Link 
                to="/signup" 
                className="w-full py-2 px-4 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors inline-block text-center"
              >
                Get Annual Plan
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <div className="bg-white py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Loved by job seekers worldwide
            </h2>
            <p className="mt-4 text-lg leading-8 text-gray-600">
              See what our users are saying about their success with ResumeAI
            </p>
          </div>
          <div className="mx-auto mt-16 flow-root max-w-2xl sm:mt-20 lg:mx-0 lg:max-w-none">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {/* Testimonial 1 */}
              <div className="rounded-2xl bg-gray-50 p-8">
                <div className="flex gap-x-4 mb-4">
                  <img className="h-12 w-12 rounded-full bg-gray-50" src="https://images.unsplash.com/photo-1494790108377-be9c29b29330" alt="" />
                  <div>
                    <h3 className="font-semibold leading-7 text-gray-900">Sarah Johnson</h3>
                    <p className="text-sm leading-6 text-gray-600">Software Engineer</p>
                  </div>
                </div>
                <p className="text-gray-700">"ResumeAI helped me land interviews at top tech companies. The AI-powered customization made my resume stand out from the crowd."</p>
              </div>
              {/* Testimonial 2 */}
              <div className="rounded-2xl bg-gray-50 p-8">
                <div className="flex gap-x-4 mb-4">
                  <img className="h-12 w-12 rounded-full bg-gray-50" src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d" alt="" />
                  <div>
                    <h3 className="font-semibold leading-7 text-gray-900">Michael Chen</h3>
                    <p className="text-sm leading-6 text-gray-600">Product Manager</p>
                  </div>
                </div>
                <p className="text-gray-700">"The automated resume tailoring saved me hours of work. I received more callbacks than ever before using ResumeAI."</p>
              </div>
              {/* Testimonial 3 */}
              <div className="rounded-2xl bg-gray-50 p-8">
                <div className="flex gap-x-4 mb-4">
                  <img className="h-12 w-12 rounded-full bg-gray-50" src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e" alt="" />
                  <div>
                    <h3 className="font-semibold leading-7 text-gray-900">David Smith</h3>
                    <p className="text-sm leading-6 text-gray-600">Marketing Director</p>
                  </div>
                </div>
                <p className="text-gray-700">"A game-changer for job seekers. The AI suggestions were spot-on and helped me highlight my most relevant experience."</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <section className="bg-indigo-600 text-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Land Your Dream Job?
          </h2>
          <p className="text-xl mb-12 max-w-2xl mx-auto">
            Join thousands of successful job seekers who have optimized their job search with our AI-powered platform.
          </p>
          <Link 
            to="/signup" 
            className="inline-flex items-center px-8 py-4 bg-white text-indigo-600 rounded-full text-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            Start Free Trial <CheckCircle className="ml-2 w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="mx-auto max-w-7xl px-6 py-12 md:flex md:items-center md:justify-between lg:px-8">
          <div className="mt-8 md:order-1 md:mt-0">
            <p className="text-center text-xs leading-5 text-gray-400">
              &copy; {new Date().getFullYear()} ResumeAI. All rights reserved.
            </p>
          </div>
          <div className="flex justify-center space-x-6 md:order-2">
            <a href="#" className="text-gray-400 hover:text-gray-300">
              <span className="sr-only">Twitter</span>
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
                <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
              </svg>
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-300">
              <span className="sr-only">GitHub</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-300">
              <span className="sr-only">LinkedIn</span>
              <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.761 0 5-2.239 5-5v-14c0-2.761-2.239-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
              </svg>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}