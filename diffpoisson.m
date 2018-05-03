function [f] = diffpoisson(scale,y,basey,minval,absrefpoint,filter,qbarrier)
mask = ~(y<0 | isnan(y));
rscale = 1./scale;
filterrsq = 1./filter.^2;
baseyscaled = basey .* rscale;
absrefpointscaled = absrefpoint .* rscale;

% Assuming square shape
side2 = sqrt(length(y(:)));

f = @(varargin)diff_func(scale, rscale,mask,y,baseyscaled, minval, absrefpointscaled, filterrsq, qbarrier, varargin{:});



function [v,x,vals] = diff_func(scale, rscale, mask, y, basey, minval, absrefpoint, filterrsq, qbarrier, x)

x = x .* rscale;
% Rescale limit by scaling to get a low gradient Lipschitz constant everywhere
lim = qbarrier .* filterrsq .* (rscale .* rscale);


% Special treatment occurs between xbase and upperlim
xbase = -basey + minval - lim ./ 2;
upperlim = xbase + lim;

subupper = x < upperlim;
xupperlim = x;
xupperlim(subupper) = upperlim(subupper);

vals = 0 * x;
absrefpointupperlim = absrefpoint - basey;
absrefpointupperlim(absrefpointupperlim<upperlim) = upperlim(absrefpointupperlim<upperlim);
absrefpointupperlim = absrefpointupperlim + basey;

% Compute log-poisson difference compared to absrefpoint, and with the log-lambda part capped at xupperlim, rather than true x (which might be less than xupperlim)
% Beyond xupperlim, extend linearly with the general 1 gradient, and a linear extrapolation of the y * ln(x) term from xupperlim
vals(mask) = -(y(mask) .* (log((xupperlim(mask) + basey(mask)) ./ max(absrefpointupperlim(mask),0.5e-9))) - 1.*(x(mask)-1*(absrefpoint(mask)-basey(mask))) - (xupperlim(mask) - x(mask)) .* (y(mask) ./ max(xupperlim(mask)+basey(mask),1e-15)) + (absrefpointupperlim(mask) - absrefpoint(mask)) .* (y(mask) ./ max(absrefpointupperlim(mask),1e-15)));

% Extra debug output
if nargout > 2
    vals2 = x;
    vals2(:) = 0;
    vals2(mask) = vals;
    vals = vals2;
end

lim2 = lim;
lim2(~mask) = lim2(~mask) * 0.5;

% Add quadratic for all low-value elements
subs = x < xbase + lim2;
limfac = ones(size(mask));
limfac(mask) = limfac(mask) + (y(mask)./max(upperlim(mask) + basey(mask),1e-15));
vals(subs) = vals(subs) + (x(subs).^2).*1./lim2(subs) .* limfac(subs);

% Compensate by quadratic from absrefpoint position, if any
subs2 = absrefpoint - basey < xbase + lim2;
%vals(subs2) = vals(subs2) - ((absrefpoint(subs2) - basey(subs2) - xbase(subs2) - lim2(subs2)).^2.*1./lim2(subs2)) .* limfac(subs2);
vals(subs2) = vals(subs2) - (absrefpoint(subs2) - basey(subs2)).^2 .* 1./lim2(subs2) .* limfac(subs2);

subs3 = subs - subs2;

vals = vals + (subs3 .* (xbase + lim2).^2 + (-subs .* x + subs2 .* (absrefpoint - basey)) .* 2 .* (xbase + lim2) ).*1./lim2 .* limfac;
v = sum(vals);

if nargout > 1
    g = y(mask)./max(xupperlim(mask) + basey(mask),1e-15) - 1;
    oldx = x;
    x(:) = 0;
    x(mask) = -g;
    if any(subs)
      x(subs) = x(subs) + 2 * (oldx(subs) - xbase(subs) - lim2(subs)).^1 .* (1./lim2(subs).^1) .* limfac(subs);
    end
    x = x .* rscale;
end

