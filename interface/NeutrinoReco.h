//copy from https://rivet.hepforge.org/analyses/CMS_2019_I1744604.html

#include "TLorentzVector.h"

#include <vector>
#include <complex>


class NeutrinoReco
{
  typedef TLorentzVector FourMomentum;

  constexpr static double WMASS = 80.4;
  constexpr static double TOPMASS = 172.5;

  public:
    static std::vector<FourMomentum> NuMomentum(
      double pxlep, double pylep, double pzlep,
      double elep, double metpx, double metpy
    ) {
      FourMomentum result(0, 0, 0, 0);
      FourMomentum result2(0, 0, 0, 0);

      double misET2 = (metpx * metpx + metpy * metpy);
      double mu = (WMASS * WMASS) / 2 + metpx * pxlep + metpy * pylep;
      double a  = (mu * pzlep) / (elep * elep - pzlep * pzlep);
      double a2 = std::pow(a, 2);

      double b  = (std::pow(elep, 2.) * (misET2) - std::pow(mu, 2.))
                  / (std::pow(elep, 2) - std::pow(pzlep, 2));

      double pz1(0), pz2(0), pznu(0), pznu2(0);

      FourMomentum p4W_rec;
      FourMomentum p4b_rec;
      FourMomentum p4Top_rec;
      FourMomentum p4lep_rec;

      p4lep_rec.SetXYZT(pxlep, pylep, pzlep, elep);

      FourMomentum p40_rec(0, 0, 0, 0);

      // there are two real solutions
      if (a2 - b > 0 ) {
        double root = sqrt(a2 - b);
        pz1 = a + root;
        pz2 = a - root;

        pznu = pz1;
        pznu2 = pz2;

        // first solution is the one with the smallest |pz|
        if (fabs(pz1) > fabs(pz2)) {
          pznu = pz2;
          pznu2 = pz1;
        }

        double Enu = sqrt(misET2 + pznu * pznu);
        double Enu2 = sqrt(misET2 + pznu2 * pznu2);

        result.SetXYZT(metpx, metpy, pznu, Enu);
        result2.SetXYZT(metpx, metpy, pznu2, Enu2);

      } else {

        // there are only complex solutions; set pz=0 and vary px/py such
        // that mT=mW while keeping px^2+py^2 close to the original pT^2
        double ptlep = sqrt(pxlep * pxlep + pylep * pylep);

        double EquationA = 1;
        double EquationB = -3 * pylep * WMASS / (ptlep);

        double EquationC = WMASS * WMASS * (2 * pylep * pylep) / (ptlep * ptlep)
                           + WMASS * WMASS
                           - 4 * pxlep * pxlep * pxlep * metpx / (ptlep * ptlep)
                           - 4 * pxlep * pxlep * pylep * metpy / (ptlep * ptlep);

        double EquationD = 4 * pxlep * pxlep * WMASS * metpy / (ptlep)
                           - pylep * WMASS * WMASS * WMASS / ptlep;

        std::vector<double> solutions = EquationSolve(EquationA, EquationB, EquationC, EquationD);

        std::vector<double> solutions2 = EquationSolve(EquationA, -EquationB, EquationC, -EquationD);

        double deltaMin = 14000 * 14000;
        double zeroValue = -WMASS * WMASS / (4 * pxlep);
        double minPx = 0;
        double minPy = 0;

        for ( size_t i = 0; i < solutions.size(); ++i) {
          if (solutions[i] < 0) continue;
          double p_x = (solutions[i] * solutions[i] - WMASS * WMASS) / (4 * pxlep);
          double p_y = (WMASS * WMASS * pylep
                        + 2 * pxlep * pylep * p_x
                        - WMASS * ptlep * solutions[i]
                        ) / (2 * pxlep * pxlep);
          double Delta2 = (p_x - metpx) * (p_x - metpx) + (p_y - metpy) * (p_y - metpy);

          if (Delta2 < deltaMin && Delta2 > 0) {
            deltaMin = Delta2;
            minPx = p_x;
            minPy = p_y;
          }

        }

        for ( size_t i = 0; i < solutions2.size(); ++i) {
          if (solutions2[i] < 0) continue;
          double p_x = (solutions2[i] * solutions2[i] - WMASS * WMASS) / (4 * pxlep);
          double p_y = (WMASS * WMASS * pylep
                        + 2 * pxlep * pylep * p_x
                        + WMASS * ptlep * solutions2[i]
                       ) / (2 * pxlep * pxlep);
          double Delta2 = (p_x - metpx) * (p_x - metpx) + (p_y - metpy) * (p_y - metpy);
          if (Delta2 < deltaMin && Delta2 > 0) {
            deltaMin = Delta2;
            minPx = p_x;
            minPy = p_y;
          }
        }

        double pyZeroValue = (WMASS * WMASS * pxlep + 2 * pxlep * pylep * zeroValue);
        double delta2ZeroValue = (zeroValue - metpx) * (zeroValue - metpx)
                                 + (pyZeroValue - metpy) * (pyZeroValue - metpy);

        if (deltaMin >= 14000 * 14000) {
          return {result};
        }

        if (delta2ZeroValue < deltaMin) {
          deltaMin = delta2ZeroValue;
          minPx = zeroValue;
          minPy = pyZeroValue;
        }


        double mu_Minimum = (WMASS * WMASS) / 2 + minPx * pxlep + minPy * pylep;
        double a_Minimum  = (mu_Minimum * pzlep) /
                            (elep * elep - pzlep * pzlep);
        pznu = a_Minimum;

        double Enu = sqrt(minPx * minPx + minPy * minPy + pznu * pznu);
        result.SetXYZT(minPx, minPy, pznu , Enu);
      }
      return {result};
    }


    /// @brief helper function find root of the cubic equation a*x^3 + b*x^2 + c*x + d = 0
    static std::vector<double> EquationSolve(
      double a, double b,
      double c, double d
    ) {

      std::vector<double> result;

      std::complex<double> x1;
      std::complex<double> x2;
      std::complex<double> x3;

      double q = (3 * a * c - b * b) / (9 * a * a);
      double r = (9 * a * b * c - 27 * a * a * d - 2 * b * b * b
                 ) / (54 * a * a * a);
      double Delta = q * q * q + r * r;

      std::complex<double> s;
      std::complex<double> t;

      double rho = 0;
      double theta = 0;

      if (Delta <= 0) {
        rho = sqrt(-(q * q * q));

        theta = acos(r / rho);

        s = std::polar<double>(sqrt(-q), theta / 3.0);
        t = std::polar<double>(sqrt(-q), -theta / 3.0);
      }

      if (Delta > 0) {
        s = std::complex<double>(cbrt(r + sqrt(Delta)), 0);
        t = std::complex<double>(cbrt(r - sqrt(Delta)), 0);
      }

      std::complex<double> i(0, 1.0);


      x1 = s + t + std::complex<double>(-b / (3.0 * a), 0);

      x2 = (s + t) * std::complex<double>(-0.5, 0)
           - std::complex<double>(b / (3.0 * a), 0)
           + (s - t) * i * std::complex<double>(sqrt(3) / 2.0, 0);

      x3 = (s + t) * std::complex<double>(-0.5, 0)
           - std::complex<double>(b / (3.0 * a), 0)
           - (s - t) * i * std::complex<double>(sqrt(3) / 2.0, 0);

      if (fabs(x1.imag()) < 0.0001) result.push_back(x1.real());
      if (fabs(x2.imag()) < 0.0001) result.push_back(x2.real());
      if (fabs(x3.imag()) < 0.0001) result.push_back(x3.real());

      return result;
    }
};
